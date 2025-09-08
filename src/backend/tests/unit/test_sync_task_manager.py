import threading
from time import sleep
from unittest.mock import patch, MagicMock

import pytest
from dispatcherd.config import setup as dispatcher_setup
from dispatcherd.worker.exceptions import DispatcherCancel

from backend.apps.dispatch.config import get_dispatcherd_config
from backend.apps.scheduler.models import JobStatusChoices, JobTypeChoices, SyncSchedule, SyncJob
from backend.apps.scheduler.task_manager import SyncTaskManager
from backend.apps.tasks.jobs import BaseTask, AAPSyncTask, AAPParseDataTask
from django.core.management import call_command

@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSyncTaskManager:

    def test_init_sets_prefix(self):
        tb = SyncTaskManager()
        assert tb.prefix == "sync_task_manager"
        assert tb.start_task_limit == 5
        assert tb.task_manager_timeout == 3

    def test_start_task_unknown_type(self):
        tb = SyncTaskManager()
        task = MagicMock()
        task.type = "UNKNOWN"
        tb.start_task(task)
        assert task.status == JobStatusChoices.FAILED
        assert "Unknown task type" in task.explanation

    @patch("backend.apps.scheduler.task_manager.AAPSyncTask")
    def test_start_task_sync_jobs(self, mock_sync_task):
        tb = SyncTaskManager()
        task = MagicMock()
        task.type = JobTypeChoices.SYNC_JOBS
        tb.start_task(task)
        mock_sync_task.apply_async.assert_called_once()

    @patch("backend.apps.scheduler.task_manager.AAPParseDataTask")
    @patch("backend.apps.scheduler.task_manager.settings")
    def test_start_task_parse_job_data(self, mock_settings, mock_parse_task):
        mock_settings.START_TASK_LIMIT = 5
        mock_settings.DISPATCHER_PARSE_CHANNEL = "parse"
        tb = SyncTaskManager()
        task = MagicMock()
        task.type = JobTypeChoices.PARSE_JOB_DATA
        tb.start_task(task)
        mock_parse_task.apply_async.assert_called_once()

    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.timed_out")
    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.start_task")
    def test_process_pending_tasks_timeout(self, mock_start_task, mock_timed_out):
        tb = SyncTaskManager()
        tb.start_task_limit = 5
        mock_timed_out.side_effect = [False, True]
        tasks = [MagicMock(), MagicMock()]
        tb.process_pending_tasks(tasks)
        # Should only process first task before timeout
        assert mock_start_task.call_count == 1

    def test_process_pending_tasks_empty(self):
        tb = SyncTaskManager()
        tb.start_task_limit = 5
        tb.process_pending_tasks([])
        # Should not call start_task
        # No assertion needed, just ensure no error

    def test_process_tasks_filters_pending(self):
        tb = SyncTaskManager()
        task_pending = MagicMock(status=JobStatusChoices.PENDING)
        task_other = MagicMock(status=JobStatusChoices.WAITING)
        tb.all_tasks = [task_pending, task_other]
        tb.process_pending_tasks = MagicMock()
        tb.process_tasks()
        tb.process_pending_tasks.assert_called_once_with([task_pending])

    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.get_tasks")
    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.process_tasks")
    def test__schedule_with_tasks(self, mock_process_tasks, mock_get_tasks):
        tb = SyncTaskManager()
        tb.all_tasks = [MagicMock()]
        tb._schedule()
        mock_process_tasks.assert_called_once()

    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.get_tasks")
    @patch("backend.apps.scheduler.task_manager.SyncTaskManager.process_tasks")
    def test__schedule_no_tasks(self, mock_process_tasks, mock_get_tasks):
        tb = SyncTaskManager()
        tb.all_tasks = []
        tb._schedule()
        mock_process_tasks.assert_not_called()

    def test_sync_schedule_job_lifecycle(self, cluster):
        # 1. Create SyncSchedule
        schedule = SyncSchedule.objects.create(
            name="Test Schedule",
            enabled=True,
            rrule="DTSTART;TZID=UTC:20240101T000000 RRULE:FREQ=MINUTELY;INTERVAL=1;COUNT=1",
            cluster=cluster,
        )
        schedule.update_computed_fields()

        # 2. Simulate the scheduler enqueuing a SyncJob (normally done by a periodic task)
        # For test, manually create a job in NEW status
        job = SyncJob.objects.create(
            name="Test Job",
            status=JobStatusChoices.NEW,
            type="Sync jobs",
            cluster=cluster,
            sync_schedule=schedule,
        )

        # 3. Signal start (should set status to PENDING)
        job.signal_start()
        job.refresh_from_db()
        assert job.status == JobStatusChoices.PENDING

        config = get_dispatcherd_config(for_service=True, mock_publish=True)
        dispatcher_setup(config=config)

        # 4. Run SyncTaskManager to process PENDING jobs (sets WAITING, triggers celery task)
        manager = SyncTaskManager()
        manager.get_tasks({'status': JobStatusChoices.PENDING})
        manager.process_tasks()
        job.refresh_from_db()
        assert job.status == JobStatusChoices.WAITING

        # 5. Simulate celery worker running the job (AAPSyncTask)
        from backend.apps.tasks.jobs import AAPSyncTask
        task = AAPSyncTask()
        task.run(job.pk)
        job.refresh_from_db()
        assert job.status in [JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED]
        assert job.started is not None
        assert job.finished is not None
        assert job.elapsed > 0

    def test_transition_status_concurrency(self, cluster):
        job = SyncJob.objects.create(
            name="Concurrent Job",
            status=JobStatusChoices.WAITING,
            type="Sync jobs",
            cluster=cluster,
        )

        results = []

        def worker():
            task = BaseTask()
            result = task.transition_status(job.pk)
            results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one should succeed, the other should return False
        assert results.count(True) == 1
        assert results.count(False) == 1

        job.refresh_from_db()
        assert job.status == JobStatusChoices.RUNNING

    def test_aapsynctask_malformed_job_args(self, cluster):
        job = SyncJob.objects.create(
            name="Malformed Args Job",
            status=JobStatusChoices.WAITING,
            type=JobTypeChoices.SYNC_JOBS,
            cluster=cluster,
            job_args="{not: valid json",  # Malformed JSON
        )
        task = AAPSyncTask()
        task.run(job.pk)
        job.refresh_from_db()
        assert job.status == JobStatusChoices.FAILED
        assert "No job args provided" in job.explanation

    @patch("backend.apps.clusters.connector.ApiConnector.check_aap_version", side_effect=Exception("API error"))
    def test_aapsynctask_api_failure(self, mock_check, cluster):
        job = SyncJob.objects.create(
            name="API Failure Job",
            status=JobStatusChoices.WAITING,
            type=JobTypeChoices.SYNC_JOBS,
            cluster=cluster,
            job_args='{}',
        )
        task = AAPSyncTask()
        task.run(job.pk)
        job.refresh_from_db()
        assert job.status == JobStatusChoices.FAILED
        assert "Error connecting to AAP API" in job.explanation

    def test_aapparsedatatask_parser_failure(self, cluster, cluster_sync_data):
        job = SyncJob.objects.create(
            name="Parser Failure Job",
            status=JobStatusChoices.WAITING,
            type=JobTypeChoices.PARSE_JOB_DATA,
            cluster=cluster,
            cluster_sync_data=cluster_sync_data,
        )
        with patch("backend.apps.clusters.parser.DataParser.parse", side_effect=Exception("Parse error")):
            task = AAPParseDataTask()
            task.run(job.pk)
        job.refresh_from_db()
        assert job.status == JobStatusChoices.FAILED
        assert "Failed to parse AAP sync data" in job.explanation

    @patch("backend.apps.clusters.connector.ApiConnector.check_aap_version", side_effect=DispatcherCancel)
    def test_aapsynctask_cancel_updates_job_state(self, mock_check, cluster):
        job = SyncJob.objects.create(
            name="API Cenceling Job",
            status=JobStatusChoices.WAITING,
            type=JobTypeChoices.SYNC_JOBS,
            cluster=cluster,
            job_args='{}',
        )
        task = AAPSyncTask()
        task.run(job.pk)
        job.refresh_from_db()
        assert job.status == JobStatusChoices.CANCELED
        assert "Canceled" in job.explanation
