from unittest.mock import patch, MagicMock

from backend.apps.tasks import system


class TestTaskSystem:

    @patch("backend.apps.tasks.system.settings")
    @patch("backend.apps.tasks.system.advisory_lock")
    @patch("backend.apps.tasks.system.SyncScheduleState")
    @patch("backend.apps.tasks.system.SyncSchedule")
    def test_automation_dashboard_periodic_scheduler_runs(
            self,
            mock_sync_schedule,
            mock_state,
            mock_lock,
            mock_settings
    ):
        mock_settings.TASK_MANAGER_LOCK_TIMEOUT = 1
        mock_lock.return_value.__enter__.return_value = True
        mock_state.get_solo.return_value.schedule_last_run = None
        mock_state.get_solo.return_value.save = MagicMock()
        mock_sync_schedule.objects.enabled.return_value.before.return_value = []
        mock_sync_schedule.objects.enabled.return_value.between.return_value = []
        system.automation_dashboard_periodic_scheduler()
        mock_state.get_solo.return_value.save.assert_called_once()

    @patch("backend.apps.tasks.system.settings")
    @patch("backend.apps.tasks.system.advisory_lock")
    def test_automation_dashboard_periodic_scheduler_lock_not_acquired(
            self,
            mock_lock,
            mock_settings
    ):
        mock_settings.TASK_MANAGER_LOCK_TIMEOUT = 1
        mock_lock.return_value.__enter__.return_value = False
        system.automation_dashboard_periodic_scheduler()

    @patch("backend.apps.tasks.system.settings")
    @patch("backend.apps.tasks.system.advisory_lock")
    @patch("backend.apps.tasks.system.SyncJob")
    def test_automation_dashboard_job_parser_data_scheduler_runs(
            self,
            mock_sync_job,
            mock_lock,
            mock_settings
    ):
        mock_settings.TASK_MANAGER_LOCK_TIMEOUT = 1
        mock_settings.SCHEDULE_MAX_DATA_PARSE_JOBS = 2
        mock_lock.return_value.__enter__.return_value = True
        job = MagicMock()
        job.cluster_sync_data = MagicMock()
        job.cluster_sync_data.cache_timeout_blocked = False
        job.signal_start.return_value = True
        mock_sync_job.objects.filter.return_value = [job]
        system.automation_dashboard_job_parser_data_scheduler()
        job.signal_start.assert_called_once()

    @patch("backend.apps.tasks.system.settings")
    @patch("backend.apps.tasks.system.advisory_lock")
    def test_automation_dashboard_job_parser_data_scheduler_lock_not_acquired(
            self,
            mock_lock,
            mock_settings
    ):
        mock_settings.TASK_MANAGER_LOCK_TIMEOUT = 1
        mock_lock.return_value.__enter__.return_value = False
        system.automation_dashboard_job_parser_data_scheduler()
