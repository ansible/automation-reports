"""
Test DB migration that fixes null-org templates.

Sets up the buggy state directly via ORM (no run_sync/run_parse),
then verifies the migration produces correct state.

AAP 2.6 API response for /api/controller/v2/jobs/<id>/ — template EXISTS:

    "summary_fields": {
        "organization": {"id": 1, "name": "Default", "description": "..."},
        "job_template": {"id": 11, "name": "jobtemplate2-org1", "description": "..."},
        ...
    },
    "job_template": 11,

AAP 2.6 API response for /api/controller/v2/jobs/<id>/ — template DELETED:

    "summary_fields": {
        "organization": {"id": 2, "name": "org2", "description": "org2-desc"},
        // job_template key is ABSENT (not null, entirely missing)
        ...
    },
    "job_template": null,

When job_template is absent from summary_fields, Pydantic defaults to None.
The parser then falls back to external_id=-1 and uses the job's own name.
"""
import importlib

import pytest
from django.apps import apps as django_apps

from backend.apps.clusters.models import (
    JobTemplate, Job, Organization, AAPUser,
)

_migration = importlib.import_module(
    "backend.apps.clusters.migrations.0027_fix_null_org_job_templates"
)
fix_null_org_job_templates = _migration.fix_null_org_job_templates


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestNullOrgTemplateMigration:

    @staticmethod
    def _create_buggy_state(cluster, template_ext_id):
        org_a = Organization.objects.create(
            cluster=cluster, external_id=100, name="Org A", description="",
        )
        org_b = Organization.objects.create(
            cluster=cluster, external_id=200, name="Org B", description="",
        )
        tmpl = JobTemplate.objects.create(
            cluster=cluster, external_id=template_ext_id, name="Deploy",
            description="", organization=None,
        )
        user = AAPUser.objects.create(
            cluster=cluster, external_id=1, name="admin", type="user",
        )
        job_defaults = dict(
            cluster=cluster, job_template=tmpl, launched_by=user,
            status="successful", job_type="run", launch_type="manual",
            failed=False, elapsed=300,
        )
        j1 = Job.objects.create(
            external_id=1, name="Deploy", organization=org_a, **job_defaults,
        )
        j2 = Job.objects.create(
            external_id=2, name="Deploy", organization=org_a, **job_defaults,
        )
        j3 = Job.objects.create(
            external_id=3, name="Deploy", organization=org_b, **job_defaults,
        )
        return {"org_a": org_a, "org_b": org_b, "tmpl": tmpl,
                "jobs": [j1, j2, j3]}

    @pytest.fixture
    def buggy_state_deleted_between_syncs(self, cluster):
        """Template deleted between sync cycles.

        Job data was fetched while template existed, so parser gets
        positive ext_id. Last-parsed job's ext_id wins (20). See
        _create_or_update_positive_id fallback in 5401a27c.
        """
        return self._create_buggy_state(cluster, template_ext_id=20)

    @pytest.fixture
    def buggy_state_never_synced(self, cluster):
        """Template deleted from AAP before first sync.

        AAP strips summary_fields.job_template from the job response,
        so parser gets external_id=-1 via the negative-id path.
        """
        return self._create_buggy_state(cluster, template_ext_id=-1)

    def test_precondition_deleted_between_syncs(self, cluster, buggy_state_deleted_between_syncs):
        """Verify buggy state: template ext_id=20, org=NULL."""
        state = buggy_state_deleted_between_syncs
        self._assert_precondition(cluster, state, expected_ext_id=20)

    def test_precondition_never_synced(self, cluster, buggy_state_never_synced):
        """Verify buggy state: template ext_id=-1, org=NULL."""
        state = buggy_state_never_synced
        self._assert_precondition(cluster, state, expected_ext_id=-1)

    def _assert_precondition(self, cluster, state, expected_ext_id):
        org_a, org_b, tmpl = state["org_a"], state["org_b"], state["tmpl"]

        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert JobTemplate.objects.filter(cluster=cluster).count() == 1
        assert Job.objects.filter(cluster=cluster).count() == 3

        assert tmpl.organization is None
        assert tmpl.name == "Deploy"
        assert tmpl.external_id == expected_ext_id

        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        for job in jobs:
            assert job.job_template == tmpl
            assert job.job_template.organization is None

        assert jobs[0].organization == org_a
        assert jobs[1].organization == org_a
        assert jobs[2].organization == org_b

    def test_migration_fixes_deleted_between_syncs(self, cluster, buggy_state_deleted_between_syncs):
        """Placeholder: template deleted between sync cycles, then parsed."""
        state = buggy_state_deleted_between_syncs
        org_a, org_b, tmpl = state["org_a"], state["org_b"], state["tmpl"]

        # Pre-migration: 1 template with org=NULL, all jobs point to it
        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert JobTemplate.objects.filter(cluster=cluster).count() == 1
        assert Job.objects.filter(cluster=cluster).count() == 3
        assert tmpl.organization is None
        assert tmpl.external_id == 20
        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        for job in jobs:
            assert job.job_template == tmpl
        assert jobs[0].organization == org_a
        assert jobs[1].organization == org_a
        assert jobs[2].organization == org_b

        fix_null_org_job_templates(django_apps, None)

        # Post-migration: 2 templates with correct orgs, null-org template deleted
        assert JobTemplate.objects.filter(cluster=cluster, organization__isnull=True).count() == 0
        assert JobTemplate.objects.filter(cluster=cluster).count() == 2

        t_a = JobTemplate.objects.get(cluster=cluster, name="Deploy", organization=org_a)
        t_b = JobTemplate.objects.get(cluster=cluster, name="Deploy", organization=org_b)
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

    def test_migration_fixes_never_synced(self, cluster, buggy_state_never_synced):
        """Template deleted from AAP before first sync."""
        state = buggy_state_never_synced
        org_a, org_b, tmpl = state["org_a"], state["org_b"], state["tmpl"]

        # Pre-migration: 1 template with org=NULL, ext_id=-1
        assert Organization.objects.filter(cluster=cluster).count() == 2
        assert JobTemplate.objects.filter(cluster=cluster).count() == 1
        assert Job.objects.filter(cluster=cluster).count() == 3
        assert tmpl.organization is None
        assert tmpl.external_id == -1
        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        for job in jobs:
            assert job.job_template == tmpl
        assert jobs[0].organization == org_a
        assert jobs[1].organization == org_a
        assert jobs[2].organization == org_b

        fix_null_org_job_templates(django_apps, None)

        # Post-migration: same expected state as deleted_between_syncs
        assert JobTemplate.objects.filter(cluster=cluster, organization__isnull=True).count() == 0
        assert JobTemplate.objects.filter(cluster=cluster).count() == 2

        t_a = JobTemplate.objects.get(cluster=cluster, name="Deploy", organization=org_a)
        t_b = JobTemplate.objects.get(cluster=cluster, name="Deploy", organization=org_b)

        jobs = Job.objects.filter(cluster=cluster).order_by('external_id')
        assert jobs.count() == 3
        assert jobs[0].job_template == t_a
        assert jobs[0].organization == org_a
        assert jobs[0].job_template.organization == org_a

        assert jobs[1].job_template == t_a
        assert jobs[1].organization == org_a

        assert jobs[2].job_template == t_b
        assert jobs[2].organization == org_b
        assert jobs[2].job_template.organization == org_b
