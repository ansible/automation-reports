from unittest.mock import patch, MagicMock

import pytest

from backend.apps.scheduler.models import JobStatusChoices, JobTypeChoices
from backend.apps.scheduler.task_manager import SyncTaskManager


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
