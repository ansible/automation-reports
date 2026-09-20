"""
Reproduce the null-organization bug on JobTemplate.

When templates are deleted from AAP between sync cycles, the connector's
cleanup removes them from the DB (zero job references because parse hasn't
run yet). When parse finally runs, it recreates templates via
JobTemplate.create_or_update WITHOUT passing organization, producing rows
with organization=NULL.
"""
import pytest

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import (
    ClusterSyncData, JobTemplate, Job, Organization,
)
from backend.apps.clusters.parser import DataParser


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

API_ORGS = [
    {"id": 100, "type": "organization", "name": "Org A", "description": ""},
    {"id": 200, "type": "organization", "name": "Org B", "description": ""},
]

API_TEMPLATES = [
    {"id": 10, "type": "job_template", "name": "Deploy",
     "description": "", "summary_fields": {"organization": {"id": 100}}},
    {"id": 20, "type": "job_template", "name": "Deploy",
     "description": "", "summary_fields": {"organization": {"id": 200}}},
]


def _make_job(job_id, template_id, template_name, org_id, org_name):
    return {
        "id": job_id,
        "type": "job",
        "name": template_name,
        "description": "",
        "launched_by": {"id": 1, "name": "admin", "type": "user"},
        "summary_fields": {
            "organization": {"id": org_id, "name": org_name, "description": ""},
            "job_template": {"id": template_id, "name": template_name, "description": ""},
            "inventory": None,
            "execution_environment": None,
            "instance_group": None,
            "labels": {"count": 0, "results": []},
            "project": None,
        },
        "started": "2026-07-01T10:00:00Z",
        "finished": "2026-07-01T10:05:00Z",
        "created": "2026-07-01T10:00:00Z",
        "modified": "2026-07-01T10:05:00Z",
        "elapsed": 300.0,
        "failed": False,
        "status": "successful",
        "job_type": "run",
        "launch_type": "manual",
    }


def _make_job_deleted_template(job_id, template_name, org_id, org_name):
    """Job whose template was deleted from AAP.

    AAP omits job_template from summary_fields entirely (not null, absent).
    Pydantic defaults the missing field to None.
    """
    job = _make_job(job_id, None, template_name, org_id, org_name)
    del job["summary_fields"]["job_template"]
    return job


API_JOBS = [
    _make_job(1, 10, "Deploy", 100, "Org A"),
    _make_job(2, 10, "Deploy", 100, "Org A"),
    _make_job(3, 20, "Deploy", 200, "Org B"),
]

# Jobs where AAP already deleted the template — job_template is None
API_JOBS_DELETED_TEMPLATE = [
    _make_job_deleted_template(1, "Deploy", 100, "Org A"),
    _make_job_deleted_template(2, "Deploy", 100, "Org A"),
    _make_job_deleted_template(3, "Deploy", 200, "Org B"),
]


# ---------------------------------------------------------------------------
# Helpers — mirrors dbg_direct_sync / dbg_direct_parse
# ---------------------------------------------------------------------------

def run_sync(cluster, mocker, api_orgs, api_templates, api_jobs):
    """Run sync_common(org) + sync_common(job_template) + sync_jobs, fully mocked."""
    mock_get = mocker.patch(
        'backend.apps.clusters.connector.ApiConnector.execute_get',
    )
    mock_get.side_effect = [
        [iter(api_orgs)],
        [iter(api_templates)],
    ]

    connector = ApiConnector(cluster, managed=True,
                             since="2026-07-01T00:00:00+00:00",
                             until="2026-07-02T00:00:00+00:00")
    connector.sync_common('organization')
    connector.sync_common('job_template')

    mocker.patch(
        'backend.apps.clusters.connector.ApiConnector.jobs',
        return_value=api_jobs,
        new_callable=mocker.PropertyMock,
    )
    mocker.patch(
        'backend.apps.clusters.connector.ApiConnector.job_host_summaries',
        return_value=iter([]),
    )
    connector.sync_jobs()

    mocker.stopall()


def run_parse(cluster):
    """Parse all pending ClusterSyncData records, like dbg_direct_parse."""
    for csd in ClusterSyncData.objects.filter(cluster=cluster).order_by('id'):
        DataParser(csd.id).parse()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestNullOrgTemplate:

    def test_normal_flow(self, mocker, cluster):
        """Sync then parse: templates get correct organization."""
        run_sync(cluster, mocker, API_ORGS, API_TEMPLATES, API_JOBS)
        run_parse(cluster)

        assert Organization.objects.filter(cluster=cluster).count() == 2
        org_a = Organization.objects.get(cluster=cluster, external_id=100)
        org_b = Organization.objects.get(cluster=cluster, external_id=200)

        templates = JobTemplate.objects.filter(cluster=cluster).order_by('external_id')
        assert templates.count() == 2
        t10 = templates.get(external_id=10)
        t20 = templates.get(external_id=20)
        assert t10.organization == org_a
        assert t20.organization == org_b
        assert t10.name == "Deploy"
        assert t20.name == "Deploy"

        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        assert jobs.count() == 3
        j1, j2, j3 = jobs[0], jobs[1], jobs[2]

        assert j1.organization == org_a
        assert j1.job_template == t10
        assert j1.job_template.organization == org_a

        assert j2.organization == org_a
        assert j2.job_template == t10
        assert j2.job_template.organization == org_a

        assert j3.organization == org_b
        assert j3.job_template == t20
        assert j3.job_template.organization == org_b

    def test_template_deleted_before_parse(self, mocker, cluster):
        """Sync twice (template deleted in AAP), then parse → templates recreated with correct org."""
        # 1st sync: templates + jobs synced, parse jobs queued
        run_sync(cluster, mocker, API_ORGS, API_TEMPLATES, API_JOBS)

        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert JobTemplate.objects.filter(cluster=cluster).count() == 2
        assert ClusterSyncData.objects.filter(cluster=cluster).count() == 3

        # 2nd sync: templates gone from AAP, cleanup deletes them (0 jobs)
        run_sync(cluster, mocker, API_ORGS, [], [])

        assert JobTemplate.objects.filter(cluster=cluster).count() == 0

        # Parse: recreates templates with correct organization
        run_parse(cluster)

        org_a = Organization.objects.get(cluster=cluster, external_id=100)
        org_b = Organization.objects.get(cluster=cluster, external_id=200)

        templates = JobTemplate.objects.filter(cluster=cluster)
        assert templates.count() == 2
        assert templates.filter(organization__isnull=True).count() == 0

        t_a = templates.get(organization=org_a)
        t_b = templates.get(organization=org_b)
        assert t_a.name == "Deploy"
        assert t_b.name == "Deploy"

        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        assert jobs.count() == 3

        assert jobs[0].job_template == t_a
        assert jobs[0].organization == org_a
        assert jobs[0].job_template.organization == org_a

        assert jobs[1].job_template == t_a
        assert jobs[1].organization == org_a
        assert jobs[1].job_template.organization == org_a

        assert jobs[2].job_template == t_b
        assert jobs[2].organization == org_b
        assert jobs[2].job_template.organization == org_b

    def test_template_deleted_after_parse(self, mocker, cluster):
        """No bug: sync, parse (creates jobs), then sync again — templates kept."""
        # 1st sync + parse: templates have jobs
        run_sync(cluster, mocker, API_ORGS, API_TEMPLATES, API_JOBS)
        run_parse(cluster)

        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert Job.objects.filter(cluster=cluster).count() == 3
        assert JobTemplate.objects.filter(cluster=cluster).count() == 2

        org_a = Organization.objects.get(cluster=cluster, external_id=100)
        org_b = Organization.objects.get(cluster=cluster, external_id=200)

        # 2nd sync: templates gone from AAP, but cleanup skips (have jobs)
        run_sync(cluster, mocker, API_ORGS, [], [])

        templates = JobTemplate.objects.filter(cluster=cluster).order_by('external_id')
        assert templates.count() == 2

        t10 = templates.get(external_id=10)
        t20 = templates.get(external_id=20)
        assert t10.organization == org_a
        assert t20.organization == org_b

        # Jobs still have correct relationships
        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        assert jobs[0].job_template == t10
        assert jobs[0].organization == org_a
        assert jobs[0].job_template.organization == org_a

        assert jobs[1].job_template == t10
        assert jobs[1].organization == org_a
        assert jobs[1].job_template.organization == org_a

        assert jobs[2].job_template == t20
        assert jobs[2].organization == org_b
        assert jobs[2].job_template.organization == org_b

    def test_template_never_synced(self, mocker, cluster):
        """Template deleted from AAP before first sync, only jobs exist.

        AAP strips summary_fields.job_template from the job response when
        the template is deleted, so parser gets job_template=None and falls
        back to external_id=-1 with the job's own name. Parser now sets
        organization correctly from the job's summary_fields.
        """
        # Sync: orgs exist, templates already deleted, jobs have job_template=None
        run_sync(cluster, mocker, API_ORGS, [], API_JOBS_DELETED_TEMPLATE)

        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert JobTemplate.objects.filter(cluster=cluster).count() == 0
        assert ClusterSyncData.objects.filter(cluster=cluster).count() == 3

        # Parse: creates per-org templates with correct organization
        run_parse(cluster)

        org_a = Organization.objects.get(cluster=cluster, external_id=100)
        org_b = Organization.objects.get(cluster=cluster, external_id=200)

        templates = JobTemplate.objects.filter(cluster=cluster)
        assert templates.count() == 2
        assert templates.filter(organization__isnull=True).count() == 0

        t_a = templates.get(organization=org_a)
        t_b = templates.get(organization=org_b)
        assert t_a.name == "Deploy"
        assert t_b.name == "Deploy"
        assert t_a.external_id < 0
        assert t_b.external_id < 0

        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        assert jobs.count() == 3

        assert jobs[0].job_template == t_a
        assert jobs[0].organization == org_a
        assert jobs[0].job_template.organization == org_a

        assert jobs[1].job_template == t_a
        assert jobs[1].organization == org_a
        assert jobs[1].job_template.organization == org_a

        assert jobs[2].job_template == t_b
        assert jobs[2].organization == org_b
        assert jobs[2].job_template.organization == org_b
