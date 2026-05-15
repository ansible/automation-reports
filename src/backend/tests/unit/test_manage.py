import pytest

from django.core.management import call_command
from django.test import TestCase

from backend.apps.clusters.models import JobStatusChoices
from backend.apps.dispatch.management.commands.run_dispatcher import Command
from backend.apps.scheduler.models import SyncJob, JobTypeChoices


@pytest.mark.django_db
class TestResetInterruptedJobs:

    def test_resets_stuck_parse_jobs_to_failed(self, cluster):
        running = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.RUNNING, launch_type='auto')
        pending = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.PENDING, launch_type='auto')
        waiting = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.WAITING, launch_type='auto')

        Command()._reset_interrupted_jobs()

        for job in [running, pending, waiting]:
            job.refresh_from_db()
            assert job.status == JobStatusChoices.FAILED

    def test_does_not_reset_completed_parse_jobs(self, cluster):
        failed = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.FAILED, launch_type='auto')
        successful = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.SUCCESSFUL, launch_type='auto')

        Command()._reset_interrupted_jobs()

        failed.refresh_from_db()
        successful.refresh_from_db()
        assert failed.status == JobStatusChoices.FAILED
        assert successful.status == JobStatusChoices.SUCCESSFUL

    def test_does_not_reset_sync_jobs(self, cluster):
        """Only PARSE_JOB_DATA jobs should be reset; sync jobs in RUNNING state are left alone."""
        sync_running = SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.SYNC_JOBS, status=JobStatusChoices.RUNNING, launch_type='auto')

        Command()._reset_interrupted_jobs()

        sync_running.refresh_from_db()
        assert sync_running.status == JobStatusChoices.RUNNING

    def test_logs_warning_with_count_when_jobs_reset(self, cluster, caplog):
        SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.RUNNING, launch_type='auto')
        SyncJob.objects.create(cluster=cluster, type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.PENDING, launch_type='auto')

        Command()._reset_interrupted_jobs()

        assert 'Reset 2 interrupted parse job(s) to FAILED on startup' in caplog.text

    def test_no_log_when_no_stuck_jobs(self, cluster, caplog):
        Command()._reset_interrupted_jobs()

        assert 'Reset' not in caplog.text


class TestUpdatePassword(TestCase):
    @pytest.fixture(autouse=True)
    def mycapsys(self, capsys):
        self._capsys = capsys

    def test_mycommand(self):
        username = "testuser"
        call_command("createsuperuser", "--no-input", username=username, email="testuser@example.com")
        call_command("update_password", username="testuser", password="testpass")
        outlines = self._capsys.readouterr().out.splitlines()
        assert outlines[0] == "Superuser created successfully."
        assert outlines[1] == f"Password updated for user {username}."
