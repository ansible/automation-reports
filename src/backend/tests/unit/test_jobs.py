from unittest.mock import patch, MagicMock

import pytest

from backend.apps.scheduler.models import JobStatusChoices, JobTypeChoices, SyncJob
from backend.apps.tasks.jobs import AAPSyncTask, AAPParseDataTask


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestJobs:

    @patch("backend.apps.tasks.jobs.ApiConnector")
    @patch("backend.apps.tasks.jobs.AAPSyncTask.update_model")
    def test_run_task_no_job_args(self, mock_update_model, mock_connector):
        task = AAPSyncTask()
        instance = MagicMock()
        instance.get_job_args = None
        instance.name = "test"
        task.instance = instance
        task.run_task()
        mock_update_model.assert_called_with(instance.pk, status=JobStatusChoices.FAILED, explanation="No job args provided for task test")

    @patch("backend.apps.tasks.jobs.ApiConnector")
    @patch("backend.apps.tasks.jobs.AAPSyncTask.update_model")
    def test_run_task_invalid_aap_version(self, mock_update_model, mock_connector, caplog, cluster):
        task = AAPSyncTask()
        instance = MagicMock()
        instance.get_job_args = {"arg": "val"}
        instance.cluster = cluster
        task.instance = instance
        task.cluster = cluster
        connector_instance = mock_connector.return_value
        connector_instance.check_aap_version.return_value = False
        task.run_task()
        assert 'Not valid version for cluster https://localhost:8000' in caplog.text
        mock_update_model.assert_any_call(instance.pk, status=JobStatusChoices.FAILED, explanation="Not valid version for cluster https://localhost:8000.")

    @patch("backend.apps.tasks.jobs.ApiConnector")
    @patch("backend.apps.tasks.jobs.AAPSyncTask.update_model")
    def test_run_task_sync_organization_exception(self, mock_update_model, mock_connector):
        task = AAPSyncTask()
        instance = MagicMock()
        instance.get_job_args = {"arg": "val"}
        instance.cluster = MagicMock()
        instance.cluster.base_url = "url"
        task.instance = instance
        connector_instance = mock_connector.return_value
        connector_instance.check_aap_version.return_value = True
        connector_instance.sync_common.side_effect = [Exception("fail"), None]
        task.run_task()
        mock_update_model.assert_any_call(instance.pk, status=JobStatusChoices.FAILED, explanation="Failed to sync AAP Organizations.")

    @patch("backend.apps.tasks.jobs.ApiConnector")
    @patch("backend.apps.tasks.jobs.AAPSyncTask.update_model")
    def test_run_task_successful(self, mock_update_model, mock_connector):
        task = AAPSyncTask()
        instance = MagicMock()
        instance.get_job_args = {"arg": "val"}
        instance.cluster = MagicMock()
        instance.cluster.base_url = "url"
        instance.pk = 1
        task.instance = instance
        connector_instance = mock_connector.return_value
        connector_instance.check_aap_version.return_value = True
        connector_instance.sync_common.side_effect = [None, None]
        connector_instance.sync_jobs.return_value = None
        task.run_task()
        mock_update_model.assert_called_with(instance.pk, status=JobStatusChoices.SUCCESSFUL)

    @patch("backend.apps.tasks.jobs.DataParser")
    @patch("backend.apps.tasks.jobs.AAPParseDataTask.update_model")
    def test_run_task_no_sync_data(self, mock_update_model, mock_data_parser):
        task = AAPParseDataTask()
        instance = MagicMock()
        instance.cluster_sync_data = None
        instance.pk = 1
        task.instance = instance
        task.run_task()
        mock_update_model.assert_called_with(instance.pk, status=JobStatusChoices.FAILED, explanation="Synchronization data not available.")

    @patch("backend.apps.tasks.jobs.DataParser")
    @patch("backend.apps.tasks.jobs.AAPParseDataTask.update_model")
    def test_run_task_parse_exception(self, mock_update_model, mock_data_parser):
        task = AAPParseDataTask()
        sync_data = MagicMock()
        sync_data.id = 42
        instance = MagicMock()
        instance.cluster_sync_data = sync_data
        instance.pk = 1
        task.instance = instance
        parser_instance = mock_data_parser.return_value
        parser_instance.parse.side_effect = Exception("parse failed")
        task.run_task()
        mock_update_model.assert_called_with(instance.pk, status=JobStatusChoices.FAILED, explanation="Failed to parse AAP sync data: 42")

    @patch("backend.apps.tasks.jobs.DataParser")
    @patch("backend.apps.tasks.jobs.AAPParseDataTask.update_model")
    def test_run_task_successful(self, mock_update_model, mock_data_parser):
        task = AAPParseDataTask()
        sync_data = MagicMock()
        sync_data.id = 42
        instance = MagicMock()
        instance.cluster_sync_data = sync_data
        instance.pk = 1
        task.instance = instance
        parser_instance = mock_data_parser.return_value
        parser_instance.parse.return_value = None
        task.run_task()
        mock_update_model.assert_called_with(instance.pk, status=JobStatusChoices.SUCCESSFUL)

    def test_job_already_running(self, cluster):
        job = SyncJob.objects.create(
            name="Already Running Job",
            status=JobStatusChoices.RUNNING,
            type=JobTypeChoices.SYNC_JOBS,
            cluster=cluster,
        )
        task = AAPSyncTask()
        task.run(job.pk)
        job.refresh_from_db()
        assert job.status == JobStatusChoices.RUNNING
        assert job.started is not None
        assert job.finished is None
