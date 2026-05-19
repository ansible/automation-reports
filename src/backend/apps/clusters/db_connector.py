import datetime
import logging

import psycopg
import psycopg.rows
import pytz

from backend.apps.clusters.encryption import decrypt_value
from backend.apps.clusters.models import (
    AAPUser,
    Cluster,
    ClusterSyncStatus,
    ExecutionEnvironment,
    Host,
    InstanceGroup,
    Inventory,
    Job,
    JobHostSummary,
    JobLabel,
    JobLaunchTypeChoices,
    JobRunTypeChoices,
    JobStatusChoices,
    JobTemplate,
    JobTypeChoices,
    Label,
    Organization,
    Project,
)

logger = logging.getLogger('automation_dashboard.db_connector')


class DbConnector:
    """Reads job data directly from AAP's PostgreSQL database."""

    def __init__(
        self,
        cluster: Cluster,
        since: datetime.datetime | None = None,
        until: datetime.datetime | None = None,
    ):
        self.cluster = cluster
        self.until = until or datetime.datetime.now(pytz.UTC)

        # Determine since from ClusterSyncStatus or provided value
        if since is not None:
            self.since = since
        else:
            try:
                sync_status = ClusterSyncStatus.objects.get(cluster=cluster)
                self.since = sync_status.last_job_finished_date
            except ClusterSyncStatus.DoesNotExist:
                self.since = self.until - datetime.timedelta(days=1)

    def _get_connection(self):
        return psycopg.connect(
            host=self.cluster.db_host,
            port=self.cluster.db_port,
            dbname=self.cluster.db_name,
            user=self.cluster.db_user,
            password=decrypt_value(bytes(self.cluster.db_password)),
            row_factory=psycopg.rows.dict_row,
            connect_timeout=10,
        )

    def check_connection(self):
        """Test the database connection. Returns (success: bool, error: str | None)."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True, None
        except Exception as e:
            return False, str(e)

    def sync(self):
        """Main sync entry point. Connects and syncs all data."""
        logger.info(f'DbConnector: syncing cluster {self.cluster} from {self.since} to {self.until}')
        with self._get_connection() as conn:
            self._sync_organizations(conn)
            self._sync_job_templates(conn)
            self._sync_jobs(conn)
        logger.info(f'DbConnector: sync complete for cluster {self.cluster}')

    def _sync_organizations(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, COALESCE(description, '') as description"
                " FROM main_organization ORDER BY name"
            )
            rows = cur.fetchall()
        for row in rows:
            Organization.create_or_update(
                cluster=self.cluster,
                external_id=row['id'],
                name=row['name'],
                description=row['description'],
            )
        logger.info(f'DbConnector: synced {len(rows)} organizations')

    def _sync_job_templates(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ujt.id, ujt.name, COALESCE(ujt.description, '') as description,
                       ujt.organization_id
                FROM main_unifiedjobtemplate ujt
                JOIN main_jobtemplate jt ON jt.unifiedjobtemplate_ptr_id = ujt.id
                ORDER BY ujt.name
            """)
            rows = cur.fetchall()
        for row in rows:
            org = None
            if row['organization_id']:
                try:
                    org = Organization.objects.get(cluster=self.cluster, external_id=row['organization_id'])
                except Organization.DoesNotExist:
                    pass
            JobTemplate.create_or_update(
                cluster=self.cluster,
                external_id=row['id'],
                name=row['name'],
                description=row['description'],
                organization=org,
            )
        logger.info(f'DbConnector: synced {len(rows)} job templates')

    def _sync_jobs(self, conn):
        JOBS_SQL = """
            SELECT
                uj.id,
                uj.status,
                uj.failed,
                uj.started,
                uj.finished,
                uj.elapsed,
                uj.launch_type,
                uj.created,
                uj.modified,
                COALESCE(ujt.name, '') as name,
                COALESCE(ujt.description, '') as description,
                COALESCE(j.job_type, 'run') as job_type,
                uj.organization_id,
                j.job_template_id,
                j.inventory_id,
                uj.execution_environment_id,
                uj.instance_group_id,
                j.project_id,
                uj.created_by_id,
                uj.polymorphic_ctype_id
            FROM main_unifiedjob uj
            JOIN main_job j ON j.unifiedjob_ptr_id = uj.id
            LEFT JOIN main_jobtemplate jt ON jt.unifiedjobtemplate_ptr_id = j.job_template_id
            LEFT JOIN main_unifiedjobtemplate ujt ON ujt.id = j.job_template_id
            WHERE uj.finished > %(since)s
              AND uj.finished <= %(until)s
              AND uj.status IN ('successful', 'failed', 'error', 'canceled')
            ORDER BY uj.finished
        """
        with conn.cursor() as cur:
            cur.execute(JOBS_SQL, {'since': self.since, 'until': self.until})
            job_rows = cur.fetchall()

        latest_finished = None

        for row in job_rows:
            job = self._sync_single_job(conn, row)
            if job and row['finished']:
                finished = row['finished']
                if finished.tzinfo is None:
                    finished = finished.replace(tzinfo=pytz.UTC)
                if latest_finished is None or finished > latest_finished:
                    latest_finished = finished

        if latest_finished:
            ClusterSyncStatus.objects.update_or_create(
                cluster=self.cluster,
                defaults={'last_job_finished_date': latest_finished},
            )

        logger.info(f'DbConnector: synced {len(job_rows)} jobs')

    def _sync_single_job(self, conn, row):
        # Resolve foreign key objects
        org = self._get_or_create_org(row['organization_id'])
        job_template = self._get_job_template(row['job_template_id'])
        inventory = self._get_or_create_inventory(conn, row['inventory_id'])
        ee = self._get_or_create_ee(conn, row['execution_environment_id'])
        ig = self._get_or_create_instance_group(conn, row['instance_group_id'])
        project = self._get_or_create_project(conn, row['project_id'])
        launched_by = self._get_or_create_user(conn, row['created_by_id'])

        # Map status — fall back to FAILED for unrecognised values
        valid_statuses = [c.value for c in JobStatusChoices]
        status = row['status'] if row['status'] in valid_statuses else JobStatusChoices.FAILED

        # Host summary aggregates
        hs_agg = self._get_host_summary_aggregates(conn, row['id'])

        job_data = dict(
            type=JobTypeChoices.JOB,
            job_type=row['job_type'] or JobRunTypeChoices.RUN,
            launch_type=row['launch_type'] or JobLaunchTypeChoices.MANUAL,
            name=row['name'] or '',
            description=row['description'] or '',
            organization=org,
            job_template=job_template,
            inventory=inventory,
            execution_environment=ee,
            instance_group=ig,
            project=project,
            launched_by=launched_by,
            status=status,
            started=row['started'],
            finished=row['finished'],
            elapsed=row['elapsed'] or 0,
            failed=row['failed'],
            created=row['created'],
            modified=row['modified'],
            num_hosts=hs_agg['num_hosts'],
            changed_hosts_count=hs_agg['changed'],
            dark_hosts_count=hs_agg['dark'],
            failures_hosts_count=hs_agg['failures'],
            ok_hosts_count=hs_agg['ok'],
            processed_hosts_count=hs_agg['processed'],
            skipped_hosts_count=hs_agg['skipped'],
            failed_hosts_count=hs_agg['failed_count'],
            ignored_hosts_count=hs_agg['ignored'],
            rescued_hosts_count=hs_agg['rescued'],
        )

        job, _ = Job.objects.update_or_create(
            cluster=self.cluster,
            external_id=row['id'],
            defaults=job_data,
        )

        # Sync labels and host summaries
        self._sync_job_labels(conn, job, row['id'])
        self._sync_host_summaries(conn, job, row['id'])

        return job

    def _get_host_summary_aggregates(self, conn, job_id):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as num_hosts,
                       COALESCE(SUM(changed), 0) as changed,
                       COALESCE(SUM(dark), 0) as dark,
                       COALESCE(SUM(failures), 0) as failures,
                       COALESCE(SUM(ok), 0) as ok,
                       COALESCE(SUM(processed), 0) as processed,
                       COALESCE(SUM(skipped), 0) as skipped,
                       COALESCE(SUM(CASE WHEN failed THEN 1 ELSE 0 END), 0) as failed_count,
                       COALESCE(SUM(ignored), 0) as ignored,
                       COALESCE(SUM(rescued), 0) as rescued
                FROM main_jobhostsummary WHERE job_id = %(job_id)s
            """, {'job_id': job_id})
            row = cur.fetchone()
        return row or {
            'num_hosts': 0,
            'changed': 0,
            'dark': 0,
            'failures': 0,
            'ok': 0,
            'processed': 0,
            'skipped': 0,
            'failed_count': 0,
            'ignored': 0,
            'rescued': 0,
        }

    def _sync_host_summaries(self, conn, job, job_id):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT hs.id, hs.host_name, hs.host_id, hs.changed, hs.dark, hs.failures,
                       hs.ok, hs.processed, hs.skipped, hs.failed, hs.ignored, hs.rescued,
                       hs.created, hs.modified, h.name as h_name
                FROM main_jobhostsummary hs
                LEFT JOIN main_host h ON h.id = hs.host_id
                WHERE hs.job_id = %(job_id)s
            """, {'job_id': job_id})
            rows = cur.fetchall()
        for row in rows:
            host = None
            if row['host_id']:
                host, _ = Host.objects.get_or_create(
                    cluster=self.cluster,
                    external_id=row['host_id'],
                    defaults={'name': row['h_name'] or row['host_name'] or ''},
                )
            JobHostSummary.objects.update_or_create(
                job=job,
                host=host,
                host_name=row['host_name'] or '',
                defaults=dict(
                    changed=row['changed'] or 0,
                    dark=row['dark'] or 0,
                    failures=row['failures'] or 0,
                    ok=row['ok'] or 0,
                    processed=row['processed'] or 0,
                    skipped=row['skipped'] or 0,
                    failed=row['failed'] or False,
                    ignored=row['ignored'] or 0,
                    rescued=row['rescued'] or 0,
                    created=row['created'],
                    modified=row['modified'],
                ),
            )

    def _sync_job_labels(self, conn, job, job_id):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT l.id, l.name FROM main_label l
                JOIN main_unifiedjob_labels ul ON ul.label_id = l.id
                WHERE ul.unifiedjob_id = %(job_id)s
            """, {'job_id': job_id})
            rows = cur.fetchall()
        JobLabel.objects.filter(job=job).delete()
        for row in rows:
            label, _ = Label.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                defaults={'name': row['name']},
            )
            JobLabel.objects.get_or_create(job=job, label=label)

    # --- FK helpers ---

    def _get_or_create_org(self, org_id):
        if not org_id:
            return None
        try:
            return Organization.objects.get(cluster=self.cluster, external_id=org_id)
        except Organization.DoesNotExist:
            return None

    def _get_job_template(self, jt_id):
        if not jt_id:
            return None
        try:
            return JobTemplate.objects.get(cluster=self.cluster, external_id=jt_id)
        except JobTemplate.DoesNotExist:
            return None

    def _get_or_create_inventory(self, conn, inv_id):
        if not inv_id:
            return None
        try:
            return Inventory.objects.get(cluster=self.cluster, external_id=inv_id)
        except Inventory.DoesNotExist:
            pass
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM main_inventory WHERE id = %(id)s", {'id': inv_id})
            row = cur.fetchone()
        if row:
            inv, _ = Inventory.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                defaults={'name': row['name']},
            )
            return inv
        return None

    def _get_or_create_ee(self, conn, ee_id):
        if not ee_id:
            return None
        try:
            return ExecutionEnvironment.objects.get(cluster=self.cluster, external_id=ee_id)
        except ExecutionEnvironment.DoesNotExist:
            pass
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, image FROM main_executionenvironment WHERE id = %(id)s",
                {'id': ee_id},
            )
            row = cur.fetchone()
        if row:
            ee, _ = ExecutionEnvironment.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                defaults={'name': row['image'] or ''},
            )
            return ee
        return None

    def _get_or_create_instance_group(self, conn, ig_id):
        if not ig_id:
            return None
        try:
            return InstanceGroup.objects.get(cluster=self.cluster, external_id=ig_id)
        except InstanceGroup.DoesNotExist:
            pass
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, is_container_group FROM main_instancegroup WHERE id = %(id)s",
                {'id': ig_id},
            )
            row = cur.fetchone()
        if row:
            ig, _ = InstanceGroup.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                defaults={'name': row['name'], 'is_container_group': row['is_container_group']},
            )
            return ig
        return None

    def _get_or_create_project(self, conn, proj_id):
        if not proj_id:
            return None
        try:
            return Project.objects.get(cluster=self.cluster, external_id=proj_id)
        except Project.DoesNotExist:
            pass
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, COALESCE(scm_type, '') as scm_type FROM main_project WHERE id = %(id)s",
                {'id': proj_id},
            )
            row = cur.fetchone()
        if row:
            proj, _ = Project.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                defaults={'name': row['name'], 'scm_type': row['scm_type']},
            )
            return proj
        return None

    def _get_or_create_user(self, conn, user_id):
        if not user_id:
            return None
        try:
            return AAPUser.objects.get(cluster=self.cluster, external_id=user_id, type='user')
        except AAPUser.DoesNotExist:
            pass
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username FROM auth_user WHERE id = %(id)s",
                {'id': user_id},
            )
            row = cur.fetchone()
        if row:
            user, _ = AAPUser.objects.get_or_create(
                cluster=self.cluster,
                external_id=row['id'],
                type='user',
                defaults={'name': row['username']},
            )
            return user
        return None
