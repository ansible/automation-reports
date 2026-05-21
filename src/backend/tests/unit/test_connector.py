import json
import logging
from datetime import datetime
from http import HTTPStatus
from unittest.mock import PropertyMock

import pytest
import pytz
import requests as requests_lib
import time_machine
from requests import Response

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.encryption import decrypt_value
from backend.apps.clusters.models import (
    ClusterVersionChoices, Cluster, Organization, JobTemplate,
    ClusterSyncData, ClusterSyncStatus, Job, JobTypeChoices, JobStatusChoices,
)


def get_response(**kwargs):
    status_code = kwargs.get('status_code', HTTPStatus.OK)
    headers = kwargs.get('headers', {'Content-Type': 'application/json', 'X-Api-Product-Name': 'AAP'})
    data = kwargs.get('data', {'results': []})
    response = Response()
    subs = json.dumps(data)
    response.status_code = status_code
    response._content = bytes(subs, 'utf-8')
    response.headers = headers

    return response


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestConnector:

    @pytest.mark.parametrize('expected', [
        {
            'Authorization': 'Bearer <PASSWORD>',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    ])
    def test_headers(self, cluster, expected):
        connector = ApiConnector(cluster)
        headers = connector.headers
        assert headers == expected

    def test_execute_one(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            return get_response()

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        result = connector.execute_get_one(f"{cluster.base_url}{cluster.api_url}/test_endpoint")
        assert result == {'results': []}

    def test_execute_one_fail(self, mocker, caplog, cluster):
        def mocked_requests_get(*args, **kwargs):
            return get_response(**{'status_code': HTTPStatus.BAD_REQUEST})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        result = connector.execute_get_one(f"{cluster.base_url}{cluster.api_url}/test_endpoint")
        assert result is None
        assert 'GET request failed with status 400' in caplog.text

    def test_execute_wrong_version(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'AWX',
            }
            return get_response(**{'headers': headers})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        with pytest.raises(Exception) as e:
            connector.execute_get_one(f"{cluster.base_url}{cluster.api_url}/test_endpoint")
        assert str(e.value) == "Not supported product."

    def test_execute_get(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            data = {
                'next': None,
                'results': [
                    {
                        'id': 1,
                        'name': 'test1'
                    },
                    {
                        'id': 2,
                        'name': 'test2'
                    },
                ],
            }
            return get_response(**{'data': data})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        endpoint = f'{cluster.api_url}/jobs/?page_size=100&page=1&order_by=finished'
        response = connector.execute_get(endpoint=endpoint)
        for r in response:
            assert r == [{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}]

    def test_execute_get_multi_page(self, mocker, cluster):
        connector = ApiConnector(cluster)
        mock = mocker.patch("backend.apps.clusters.connector.ApiConnector.execute_get_one")
        results = [
            {'id': 1, 'name': 'test1'},
            {'id': 2, 'name': 'test2'},
            {'id': 3, 'name': 'test3'},
            {'id': 4, 'name': 'test4'},
        ]
        mock.side_effect = [
            {
                "count": 4,
                "next": "/test_endpoint?page=2",
                "results": results[0:2]
            },
            {
                "count": 4,
                "next": None,
                "results": results[2:4]
            },
        ]
        endpoint = f'{cluster.api_url}/jobs/?page_size=2&page=1&order_by=finished'
        response = connector.execute_get(endpoint=endpoint)
        data = list(response)
        assert len(data) == 2  # two pages
        assert data[0] == results[0:2]  # first page
        assert data[1] == results[2:4]  # second page

    def test_ping(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            data = {
                "version": "4.4.2",
            }
            return get_response(**{'data': data})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        url = "/api/v2/ping/"
        response = connector.ping(url)
        assert response == {'version': '4.4.2'}

    def test_detect_aap_version_25(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers, 'data': dict(version="2.5")})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        assert connector.detect_aap_version() == ClusterVersionChoices.AAP25

    def test_detect_aap_version_24(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', side_effect=[None, mocked_requests_get()])
        assert connector.detect_aap_version() == ClusterVersionChoices.AAP24

    def test_check_aap_version_24(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.detect_aap_version', return_value="AAP 2.4")
        connector = ApiConnector(cluster)
        connector.check_aap_version()
        assert Cluster.objects.first().aap_version == ClusterVersionChoices.AAP24

    def test_check_aap_version_25(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.detect_aap_version', return_value="AAP 2.5")
        connector = ApiConnector(cluster)
        connector.check_aap_version()
        assert Cluster.objects.first().aap_version == ClusterVersionChoices.AAP25

    def test_check_aap_version_fail(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.detect_aap_version', side_effect=Exception('Not valid version for cluster https://localhost:8000.'), new_callable=mocker.PropertyMock)
        connector = ApiConnector(cluster)
        with pytest.raises(Exception) as e:
            connector.check_aap_version()
        assert str(e.value) == "Not valid version for cluster https://localhost:8000."

    @pytest.mark.parametrize('expected', [
        [
            {"name": "Organization B", "description": "", "cluster_id": 1, "external_id": 1},
            {"name": "Organization A", "description": "Description for organization A", "cluster_id": 1, "external_id": 2},
            {"name": "Organization C", "description": "Description for organization C", "cluster_id": 1, "external_id": 3},
            {"name": "Organization D", "description": "Description for organization D", "cluster_id": 1, "external_id": 4},
        ]
    ])
    def test_sync_organizations(self, mocker, cluster, organizations, api_organizations, expected):
        mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.execute_get')
        mock.side_effect = [[iter(api_organizations)]]
        connector = ApiConnector(cluster)
        connector.sync_common(sync_type='organization')
        db_data = Organization.objects.all()
        assert len(db_data) == 4
        for i, expected_obj in enumerate(expected):
            for key, value in expected_obj.items():
                assert getattr(db_data[i], key) == value

    @pytest.mark.parametrize('expected', [
        [
            {"name": "Job Template A", "description": "", "cluster_id": 1, "external_id": 1},
            {"name": "Job Template B", "description": "Description for job template B", "cluster_id": 1, "external_id": 2},
            {"name": "Job Template C", "description": "", "cluster_id": 1, "external_id": 4},
            {"name": "Job Template D", "description": "Description for job template D", "cluster_id": 1, "external_id": 5},
            {"name": "Job Template E", "description": "Description for job template E", "cluster_id": 1, "external_id": 6},
        ]
    ])
    def test_sync_job_templates(self, mocker, cluster, job_templates, api_job_templates, expected):
        mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.execute_get')
        mock.side_effect = [[iter(api_job_templates)]]
        connector = ApiConnector(cluster)
        connector.sync_common(sync_type='job_template')
        db_data = JobTemplate.objects.all()
        assert len(db_data) == 5
        for i, expected_obj in enumerate(expected):
            for key, value in expected_obj.items():
                assert getattr(db_data[i], key) == value

    def test_sync_common_not_implemented(self, cluster):
        connector = ApiConnector(cluster)
        with pytest.raises(NotImplementedError):
            connector.sync_common(sync_type='foo')

    def test_sync_job_templates_deletion_with_jobs(self, mocker, cluster, caplog):
        """Test that templates deleted from AAP but with job references are skipped, not deleted."""
        import logging

        # Create templates in DB: one with jobs, one without
        template_with_jobs = JobTemplate.objects.create(
            name="Template With Jobs",
            cluster=cluster,
            external_id=100,
            description="Has job references"
        )
        template_without_jobs = JobTemplate.objects.create(
            name="Template Without Jobs",
            cluster=cluster,
            external_id=101,
            description="No job references"
        )

        # Create a job referencing the first template
        Job.objects.create(
            type=JobTypeChoices.JOB,
            name="Test Job",
            job_template=template_with_jobs,
            cluster=cluster,
            external_id=999,
            status=JobStatusChoices.SUCCESSFUL,
            started=datetime(2025, 1, 1, 10, 0, 0, tzinfo=pytz.UTC),
            finished=datetime(2025, 1, 1, 10, 5, 0, tzinfo=pytz.UTC),
        )

        # Mock API response - returns empty list (both templates deleted from AAP)
        mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.execute_get')
        mock.side_effect = [[iter([])]]

        connector = ApiConnector(cluster)

        # Capture logs
        with caplog.at_level(logging.INFO):
            connector.sync_common(sync_type='job_template')

        # Template without jobs should be deleted
        assert not JobTemplate.objects.filter(external_id=101).exists()
        assert "Deleting job template Template Without Jobs" in caplog.text

        # Template with jobs should still exist (skipped)
        assert JobTemplate.objects.filter(external_id=100).exists()

        # Should log about skipped deletion
        assert "Skipped deletion of 1 templates deleted from AAP but DB retains them with job references" in caplog.text

    def test_jobs(self, mocker, cluster):
        return_items = [{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}]
        mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.execute_get')
        mock.side_effect = [[iter(return_items)]]
        connector = ApiConnector(cluster)
        jobs = connector.jobs
        assert list(jobs) == return_items

    @pytest.mark.parametrize('expected', [
        [
            {
                "cluster_id": 1,
                "data": {
                    'id': 1,
                    'name': 'Job Template A',
                    'type': 'job',
                    'failed': False,
                    'status': 'successful',
                    'created': '2025-04-05T18:30:02.730338Z',
                    'elapsed': 8.263,
                    'started': '2025-04-05T18:30:03.963413Z',
                    'finished': '2025-04-05T18:30:12.226281Z',
                    'job_type': 'run',
                    'modified': '2025-04-05T18:30:03.739997Z',
                    'description': '',
                    'launch_type': 'manual',
                    'launched_by': {
                        'id': 1,
                        'name': 'AAP User',
                        'type': 'user'
                    },
                    'host_summaries': [
                        {
                            'id': 1,
                            'ok': 3,
                            'dark': 0,
                            'failed': False,
                            'changed': 0,
                            'created': '2025-04-05T18:30:02.851402Z',
                            'ignored': 0,
                            'rescued': 0,
                            'skipped': 0,
                            'failures': 0,
                            'modified': '2025-04-05T18:30:02.851402Z',
                            'host_name': 'Host A',
                            'processed': 1,
                            'summary_fields': {
                                'host': {
                                    'id': 1,
                                    'name': 'Host A',
                                    'description': ''
                                }
                            }
                        }
                    ],
                    'summary_fields': {
                        'labels': {
                            'count': 1,
                            'results': [
                                {
                                    'id': 1,
                                    'name':
                                        'Label A'
                                }
                            ]
                        },
                        'project': {
                            'id': 1,
                            'name': 'Project A',
                            'scm_type': '',
                            'description': ''
                        },
                        'inventory': {
                            'id': 1,
                            'name': 'Inventory A',
                            'description': 'Description for inventory A'
                        },
                        'job_template': {
                            'id': 1,
                            'name': 'Job Template A',
                            'type': 'job_template',
                            'description': ''
                        },
                        'organization': {
                            'id': 1,
                            'name': 'Organization B',
                            'type': 'organization',
                            'description': ''
                        },
                        'instance_group': {
                            'id': 1,
                            'name': 'Instance Group A',
                            'is_container_group': False
                        },
                        'execution_environment': {
                            'id': 1,
                            'name': 'Execution Environment',
                            'description': 'Execution Environment description'
                        }
                    }
                }
            },
            {
                "cluster_id": 1,
                "data": {
                    'id': 2,
                    'name': 'Job Template B',
                    'type': 'job',
                    'failed': False,
                    'status': 'successful',
                    'created': '2025-04-05T18:30:02.851402Z',
                    'elapsed': 8.263,
                    'started': '2025-04-05T18:30:03.963413Z',
                    'finished': '2025-04-05T18:30:12.226281Z',
                    'job_type': 'run',
                    'modified': '2025-04-05T18:30:03.739997Z',
                    'description': '',
                    'launch_type': 'manual',
                    'launched_by': {
                        'id': 1,
                        'name': 'AAP User',
                        'type': 'user'
                    },
                    'host_summaries': [
                        {
                            'id': 2,
                            'ok': 2,
                            'dark': 0,
                            'failed': False,
                            'changed': 0,
                            'created': '2025-04-05T18:30:02.851402Z',
                            'ignored': 0,
                            'rescued': 0,
                            'skipped': 0,
                            'failures': 0,
                            'modified': '2025-04-05T18:30:02.851402Z',
                            'host_name': 'Host B',
                            'processed': 1,
                            'summary_fields': {
                                'host': {
                                    'id': 2,
                                    'name': 'Host B',
                                    'description': ''
                                }
                            }
                        },
                        {
                            'id': 3,
                            'ok': 4,
                            'dark': 0,
                            'failed': False,
                            'changed': 0,
                            'created': '2025-04-05T18:30:02.851402Z',
                            'ignored': 0,
                            'rescued': 0,
                            'skipped': 0,
                            'failures': 0,
                            'modified': '2025-04-05T18:30:02.851402Z',
                            'host_name': 'Host C',
                            'processed': 1,
                            'summary_fields': {
                                'host': {
                                    'id': 3,
                                    'name': 'Host C',
                                    'description': ''
                                }
                            }
                        }
                    ],
                    'summary_fields': {
                        'labels': {
                            'count': 2,
                            'results': [
                                {
                                    'id': 2,
                                    'name': 'Label B'
                                },
                                {
                                    'id': 3,
                                    'name': 'Label C'
                                }
                            ]
                        },
                        'project': {
                            'id': 2,
                            'name': 'Project B',
                            'scm_type': '',
                            'description': 'Project B description'
                        },
                        'inventory': {
                            'id': 1,
                            'name': 'Inventory A',
                            'description': 'Description for inventory A'
                        },
                        'job_template': {
                            'id': 2,
                            'name': 'Job Template B',
                            'type': 'job_template',
                            'description': 'Description for job template B'
                        },
                        'organization': {
                            'id': 2,
                            'name': 'Organization A',
                            'type': 'organization',
                            'description': 'Description for organization A'
                        },
                        'instance_group': {
                            'id': 1,
                            'name': 'Instance Group A',
                            'is_container_group': False
                        },
                        'execution_environment': {
                            'id': 1,
                            'name': 'Execution Environment',
                            'description': 'Execution Environment description'
                        }
                    }
                }
            }
        ]
    ])
    def test_sync(self, mocker, cluster, api_jobs, api_host_summaries, expected):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.sync_common')
        mocker.patch('backend.apps.clusters.connector.ApiConnector.check_aap_version')
        mocker.patch('backend.apps.clusters.parser.DataParser.parse', return_value=None)
        mocker.patch('backend.apps.clusters.connector.ApiConnector.jobs', return_value=api_jobs, new_callable=mocker.PropertyMock)
        host_summaries_mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.job_host_summaries')
        host_summaries_mock.side_effect = [
            [api_host_summaries[0]],
            [api_host_summaries[1], api_host_summaries[2]],
        ]
        connector = ApiConnector(cluster)
        connector.sync_jobs()
        db_data = ClusterSyncData.objects.all()
        assert len(db_data) == 2

        for i, data in enumerate(db_data):
            assert data.cluster_id == expected[i]['cluster_id']
            assert dict(data.data) == expected[i]['data']

    def test_since_iso_date(self, settings, cluster):
        settings.INITIAL_SYNC_SINCE = '2025-05-06'
        connector = ApiConnector(cluster)
        assert str(connector.since) == '2025-05-06 00:00:00+00:00'

    @time_machine.travel(datetime(2025, 10, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_since_without_iso_date(self, settings, cluster):
        delattr(settings, "INITIAL_SYNC_SINCE")
        settings.INITIAL_SYNC_DAYS = 5
        connector = ApiConnector(cluster)
        assert str(connector.since) == '2025-10-16 00:00:00+00:00'
        assert connector.until is None

    @time_machine.travel(datetime(2025, 10, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_since_without_iso_date_without_timedelta_days(self, settings, cluster):
        delattr(settings, "INITIAL_SYNC_SINCE")
        delattr(settings, "INITIAL_SYNC_DAYS")
        connector = ApiConnector(cluster)
        assert str(connector.since) == '2025-10-20 00:00:00+00:00'
        assert connector.until is None

    def test_since_until(self, cluster):
        since = datetime(2025, 10, 1, 22, 1, 45, tzinfo=pytz.UTC)
        until = datetime(2025, 10, 31, 22, 1, 45, tzinfo=pytz.UTC)
        since = datetime.combine(since, datetime.min.time()).astimezone(pytz.UTC)
        until = datetime.combine(until, datetime.max.time()).astimezone(pytz.UTC)
        connector = ApiConnector(cluster, since=since, until=until)
        assert str(connector.since) == '2025-10-01 00:00:00+00:00'
        assert str(connector.until) == '2025-10-31 23:59:59.999999+00:00'

    def test_sync_jobs_null_started_is_ingested_and_logged(self, mocker, cluster, caplog):
        """A job with started=null must be stored in ClusterSyncData and produce an info log."""
        job = {
            "id": 99,
            "finished": "2025-01-16T20:44:21.000000Z",
            "started": None,
            "status": "failed",
        }
        connector = ApiConnector(cluster)
        mocker.patch.object(type(connector), 'jobs', new_callable=PropertyMock, return_value=[job])
        mocker.patch.object(connector, 'job_host_summaries', return_value=iter([]))

        with caplog.at_level(logging.INFO, logger='automation_dashboard.clusters.connector'):
            connector.sync_jobs()

        assert 'has null started time' in caplog.text
        assert ClusterSyncData.objects.filter(cluster=cluster, data__id=99).exists()

    def test_sync_jobs_missing_finished_is_skipped(self, mocker, cluster, caplog):
        """A job without a finished timestamp must be skipped and not stored."""
        job = {"id": 100, "finished": None, "started": "2025-01-16T20:00:00.000000Z", "status": "running"}
        connector = ApiConnector(cluster)
        mocker.patch.object(type(connector), 'jobs', new_callable=PropertyMock, return_value=[job])

        with caplog.at_level(logging.WARNING, logger='automation_dashboard.clusters.connector'):
            connector.sync_jobs()

        assert 'Missing id or finished date time' in caplog.text
        assert not ClusterSyncData.objects.filter(cluster=cluster, data__id=100).exists()

    # ------------------------------------------------------------------
    # _reauthorize
    # ------------------------------------------------------------------

    def test_reauthorize_success(self, mocker, cluster):
        """_reauthorize should update cluster tokens from a successful POST response."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps({
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
        }).encode('utf-8')

        mocker.patch('requests.post', return_value=mock_response)

        connector = ApiConnector(cluster)
        result = connector._reauthorize()

        assert result is True
        assert connector.access_token == 'new_access_token'
        cluster.refresh_from_db()
        assert decrypt_value(cluster.access_token) == 'new_access_token'
        assert decrypt_value(cluster.refresh_token) == 'new_refresh_token'

    def test_reauthorize_post_request_exception(self, mocker, cluster):
        """_reauthorize should return False if POST raises a RequestException."""
        mocker.patch('requests.post', side_effect=requests_lib.exceptions.RequestException('Timeout'))
        connector = ApiConnector(cluster)
        result = connector._reauthorize()
        assert result is False

    def test_reauthorize_non_ok_response(self, mocker, cluster, caplog):
        """_reauthorize should return False if POST returns a non-OK status."""
        mock_response = Response()
        mock_response.status_code = 400
        mock_response._content = b'Bad Request'

        mocker.patch('requests.post', return_value=mock_response)

        connector = ApiConnector(cluster)
        with caplog.at_level(logging.ERROR, logger='automation_dashboard.clusters.connector'):
            result = connector._reauthorize()

        assert result is False
        assert 'Token refresh POST request failed with status 400' in caplog.text

    # ------------------------------------------------------------------
    # _get_with_reauth
    # ------------------------------------------------------------------

    def test_get_with_reauth_retries_after_401(self, mocker, cluster):
        """On 401, _get_with_reauth re-authorizes and retries; second response is returned."""
        response_401 = Response()
        response_401.status_code = 401
        response_401._content = b'Unauthorized'

        response_ok = get_response()  # 200 OK

        mocker.patch('requests.get', side_effect=[response_401, response_ok])
        mocker.patch(
            'backend.apps.clusters.connector.ApiConnector._reauthorize',
            return_value=True,
        )

        connector = ApiConnector(cluster)
        result = connector._get_with_reauth(f"{cluster.base_url}/test")
        assert result is not None
        assert result.status_code == 200

    def test_get_with_reauth_request_exception_returns_none(self, mocker, cluster, caplog):
        """A plain RequestException (not ConnectionError) on first GET must return None."""
        mocker.patch(
            'requests.get',
            side_effect=requests_lib.exceptions.Timeout('Timed out'),
        )
        connector = ApiConnector(cluster)
        with caplog.at_level(logging.ERROR, logger='automation_dashboard.clusters.connector'):
            result = connector._get_with_reauth(f"{cluster.base_url}/test")
        assert result is None

    def test_get_with_reauth_reraises_responses_connection_error(self, mocker, cluster):
        """A ConnectionError from the `responses` library must be re-raised."""
        error = requests_lib.exceptions.ConnectionError(
            "Connection refused by Responses - the call doesn't match any registered mock."
        )
        mocker.patch('requests.get', side_effect=error)

        connector = ApiConnector(cluster)
        with pytest.raises(requests_lib.exceptions.ConnectionError) as exc_info:
            connector._get_with_reauth(f"{cluster.base_url}/test")
        assert 'Connection refused by Responses' in str(exc_info.value)

    def test_get_with_reauth_second_request_exception_returns_none(self, mocker, cluster, caplog):
        """RequestException on the *retry* GET (after 401) must return None."""
        response_401 = Response()
        response_401.status_code = 401
        response_401._content = b'Unauthorized'

        mocker.patch(
            'requests.get',
            side_effect=[response_401, requests_lib.exceptions.Timeout('Timed out again')],
        )
        mocker.patch(
            'backend.apps.clusters.connector.ApiConnector._reauthorize',
            return_value=True,
        )

        connector = ApiConnector(cluster)
        result = connector._get_with_reauth(f"{cluster.base_url}/test")
        assert result is None

    # ------------------------------------------------------------------
    # execute_get_one / execute_get
    # ------------------------------------------------------------------

    def test_execute_get_one_returns_none_when_no_response(self, mocker, cluster):
        """execute_get_one should return None when _get_with_reauth returns None."""
        mocker.patch(
            'backend.apps.clusters.connector.ApiConnector._get_with_reauth',
            return_value=None,
        )
        connector = ApiConnector(cluster)
        result = connector.execute_get_one(f"{cluster.base_url}/test")
        assert result is None

    def test_execute_get_none_response_yields_empty_list(self, mocker, cluster):
        """execute_get should yield an empty list when execute_get_one returns None."""
        mocker.patch(
            'backend.apps.clusters.connector.ApiConnector.execute_get_one',
            return_value=None,
        )
        connector = ApiConnector(cluster)
        results = list(connector.execute_get(endpoint='/api/v2/test/'))
        assert results == [[]]

    # ------------------------------------------------------------------
    # job_host_summaries
    # ------------------------------------------------------------------

    def test_job_host_summaries(self, mocker, cluster):
        """job_host_summaries should yield all summaries returned by the API."""
        summaries = [
            {'id': 1, 'host_name': 'Host A'},
            {'id': 2, 'host_name': 'Host B'},
        ]
        mock = mocker.patch('backend.apps.clusters.connector.ApiConnector.execute_get')
        mock.side_effect = [[iter(summaries)]]
        connector = ApiConnector(cluster)
        result = list(connector.job_host_summaries(42))
        assert result == summaries

    # ------------------------------------------------------------------
    # detect_aap_version  (additional scenarios)
    # ------------------------------------------------------------------

    def test_detect_aap_version_26(self, mocker, cluster):
        """detect_aap_version should return AAP26 when the gateway returns version 2.6."""
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers, 'data': {'version': '2.6'}})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        assert connector.detect_aap_version() == ClusterVersionChoices.AAP26

    def test_detect_aap_version_unknown_version_raises(self, mocker, cluster):
        """detect_aap_version should raise when the gateway responds with an unknown version."""
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers, 'data': {'version': '9.9'}})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        with pytest.raises(Exception) as exc_info:
            connector.detect_aap_version()
        assert 'Not valid version' in str(exc_info.value)

    def test_detect_aap_version_both_pings_fail_raises(self, mocker, cluster):
        """detect_aap_version should raise when both gateway and v2 pings return None."""
        mocker.patch(
            'backend.apps.clusters.connector.ApiConnector.ping',
            return_value=None,
        )
        connector = ApiConnector(cluster)
        with pytest.raises(Exception) as exc_info:
            connector.detect_aap_version()
        assert 'Not valid version' in str(exc_info.value)

    # ------------------------------------------------------------------
    # __init__ – edge-case since / managed logic
    # ------------------------------------------------------------------

    def test_init_managed_uses_provided_since(self, cluster):
        """In managed mode the connector must use the explicitly provided `since` value."""
        since = datetime(2025, 5, 1, tzinfo=pytz.UTC)
        connector = ApiConnector(cluster, since=since, managed=True)
        assert connector.since == since
        assert connector.managed is True

    @pytest.mark.django_db(transaction=True)
    def test_init_uses_last_job_finished_date_from_sync_status(self, cluster):
        """Without an explicit `since`, the connector should fall back to the last sync date."""
        last_date = datetime(2025, 3, 15, 12, 0, 0, tzinfo=pytz.UTC)
        ClusterSyncStatus.objects.create(cluster=cluster, last_job_finished_date=last_date)
        connector = ApiConnector(cluster)
        assert connector.since == last_date

    @time_machine.travel(datetime(2025, 10, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_since_invalid_iso_date_falls_back_to_timedelta(self, settings, cluster):
        """An unparseable INITIAL_SYNC_SINCE must fall back to now() – INITIAL_SYNC_DAYS."""
        settings.INITIAL_SYNC_SINCE = 'not-a-valid-date'
        settings.INITIAL_SYNC_DAYS = 7
        connector = ApiConnector(cluster)
        assert str(connector.since) == '2025-10-14 00:00:00+00:00'

    # ------------------------------------------------------------------
    # sync_jobs – invalid finished format
    # ------------------------------------------------------------------

    def test_sync_jobs_invalid_finished_format_raises(self, mocker, cluster):
        """sync_jobs must raise TypeError when the `finished` field is not ISO-8601."""
        job = {
            'id': 77,
            'finished': 'not-a-date',
            'started': '2025-01-16T20:00:00.000000Z',
            'status': 'successful',
        }
        connector = ApiConnector(cluster)
        mocker.patch.object(type(connector), 'jobs', new_callable=PropertyMock, return_value=[job])

        with pytest.raises(TypeError):
            connector.sync_jobs()

    # ------------------------------------------------------------------
    # ping – request exception
    # ------------------------------------------------------------------

    def test_ping_request_exception_returns_none(self, mocker, cluster, caplog):
        """ping() must return None and log the exception on a RequestException."""
        mocker.patch(
            'requests.get',
            side_effect=requests_lib.exceptions.Timeout('Connection timed out'),
        )
        connector = ApiConnector(cluster)
        with caplog.at_level(logging.ERROR, logger='automation_dashboard.clusters.connector'):
            result = connector.ping('/api/v2/ping/')
        assert result is None

