import json

from requests import Response
from http import HTTPStatus
import pytest

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterVersionChoices, Cluster, Organization, JobTemplate, Job, ClusterSyncData


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

    def test_is_aap25_instance(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        assert connector.is_aap25_instance is True

    def test_is_aap24_instance(self, mocker, cluster):
        def mocked_requests_get(*args, **kwargs):
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Product-Name': 'Red Hat Ansible Automation Platform',
            }
            return get_response(**{'headers': headers})

        connector = ApiConnector(cluster)
        mocker.patch('requests.get', new=mocked_requests_get)
        assert connector.is_aap24_instance is True

    def test_check_aap_version_24(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap25_instance', return_value=False, new_callable=mocker.PropertyMock)
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap24_instance', return_value=True, new_callable=mocker.PropertyMock)
        connector = ApiConnector(cluster)
        connector.check_aap_version()
        assert Cluster.objects.first().aap_version == ClusterVersionChoices.AAP24

    def test_check_aap_version_25(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap25_instance', return_value=True, new_callable=mocker.PropertyMock)
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap24_instance', return_value=False, new_callable=mocker.PropertyMock)
        connector = ApiConnector(cluster)
        connector.check_aap_version()
        assert Cluster.objects.first().aap_version == ClusterVersionChoices.AAP25

    def test_check_aap_version_fail(self, mocker, cluster):
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap25_instance', return_value=False, new_callable=mocker.PropertyMock)
        mocker.patch('backend.apps.clusters.connector.ApiConnector.is_aap24_instance', return_value=False, new_callable=mocker.PropertyMock)
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
        connector.sync()
        db_data = ClusterSyncData.objects.all()
        assert len(db_data) == 2

        for i, data in enumerate(db_data):
            assert data.cluster_id == expected[i]['cluster_id']
            assert dict(data.data) == expected[i]['data']
