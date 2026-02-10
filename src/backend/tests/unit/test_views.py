import csv
import io
import json
from datetime import datetime
from unittest import mock

import pytest
import pytz
import time_machine
from rest_framework.test import APIClient

from backend.api.v1.ping.views import PingView
from backend.apps.clusters.models import Project, JobTemplate, Costs, CostsChoices
from backend.apps.common.models import FilterSet, Currency, Settings, SettingsChoices

test_template_option_expected_data = {
    'clusters': [
        {'id': 1, 'address': 'localhost'}
    ],
    'currencies': [
        {'id': 2, 'name': 'EUR', 'iso_code': 'EUR', 'symbol': '€'},
        {'id': 1, 'name': 'United States Dollar', 'iso_code': 'USD', 'symbol': '$'}
    ],
    'date_ranges': [
        {'key': 'last_year', 'value': 'Past year'},
        {'key': 'last_6_month', 'value': 'Past 6 months'},
        {'key': 'last_3_month', 'value': 'Past 3 months'},
        {'key': 'last_month', 'value': 'Past month'},
        {'key': 'year_to_date', 'value': 'Year to date'},
        {'key': 'quarter_to_date', 'value': 'Quarter to date'},
        {'key': 'month_to_date', 'value': 'Month to date'},
        {'key': 'last_3_years', 'value': 'Past 3 years'},
        {'key': 'last_2_years', 'value': 'Past 2 years'},
        {'key': 'custom', 'value': 'Custom'}
    ],
    'manual_cost_automation_per_hour': '3000.00',
    'automated_process_cost_per_minute': '20.00',
    'currency': 1,
    'enable_template_creation_time': True,
    'filter_sets': [
        {
            'id': 1,
            'name': 'Report 1',
            'filters': {
                'date_range': 'last_month',
                'organization': [1, 2]
            }
        },
        {
            'id': 2,
            'name': 'Report 2',
            'filters': {
                'template': [1, 2],
                'date_range': 'last_year'
            }
        }
    ],
    'max_pdf_job_templates': 4000
}

test_report_expected_data = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'name': 'Job Template A',
            'runs': 1,
            'elapsed': '25.00',
            'cluster': 1,
            'elapsed_str': '0min 25sec',
            'num_hosts': 2,
            'time_taken_manually_execute_minutes': 60,
            'time_taken_create_automation_minutes': 60,
            'successful_runs': 1,
            'failed_runs': 0,
            'automated_costs': '3008.33',
            'manual_costs': '6000.00',
            'savings': '2991.67',
            'job_template_id': 1,
            'time_savings': '3575.00',
            'time_savings_str': '59min 35sec'
        }
    ]
}

test_report_past_month_expected_data = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'name': 'Job Template B',
            'runs': 1,
            'elapsed': '25.00',
            'cluster': 1,
            'elapsed_str': '0min 25sec',
            'num_hosts': 2,
            'time_taken_manually_execute_minutes': 60,
            'time_taken_create_automation_minutes': 60,
            'successful_runs': 1,
            'failed_runs': 0,
            'automated_costs': '3008.33',
            'manual_costs': '6000.00',
            'savings': '2991.67',
            'job_template_id': 2,
            'time_savings': '3575.00',
            'time_savings_str': '59min 35sec'
        }
    ]
}

test_report_details_expected_data = {
    'total_number_of_unique_hosts': {
        'value': 3
    },
    'total_number_of_successful_jobs': {
        'value': 2
    },
    'total_number_of_failed_jobs': {
        'value': 0
    },
    'total_number_of_job_runs': {
        'value': 2
    },
    'total_number_of_host_job_runs': {
        'value': 4
    },
    'total_hours_of_automation': {
        'value': 0.01
    },
    'cost_of_automated_execution': {
        'value': 6016.67
    },
    'cost_of_manual_automation': {
        'value': 12000.0
    },
    'total_saving': {
        'value': 5983.33
    },
    'total_time_saving': {
        'value': 1.99
    },
    'users': [
        {'user_id': 1, 'user_name': 'AAP User', 'count': 2}
    ],
    'projects': [
        {'project_id': 1, 'project_name': 'Project A', 'count': 2}
    ],
    'host_chart': {
        'items': [
            {'x': '2025-01-01T00:00:00Z', 'y': 0},
            {'x': '2025-02-01T00:00:00Z', 'y': 2},
            {'x': '2025-03-01T00:00:00Z', 'y': 2}
        ],
        'range': 'month'
    },
    'job_chart': {
        'items': [
            {'x': '2025-01-01T00:00:00Z', 'y': 0},
            {'x': '2025-02-01T00:00:00Z', 'y': 1},
            {'x': '2025-03-01T00:00:00Z', 'y': 1}],
        'range': 'month'
    },
    'related_links': {
        'successful_jobs': 'https://localhost:8000/#/jobs?job.finished__gte=2025-01-01T00%3A00%3A00%2B00%3A00&job.finished__lte=2025-03-21T23%3A59%3A59.999999%2B00%3A00&job.status__exact=successful',
        'failed_jobs': 'https://localhost:8000/#/jobs?job.status__exact=failed&job.finished__gte=2025-01-01T00%3A00%3A00%2B00%3A00&job.finished__lte=2025-03-21T23%3A59%3A59.999999%2B00%3A00'},
}

test_report_disabled_time_taken_to_create_automation_save_expected_data = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'name': 'Job Template B',
            'runs': 1,
            'elapsed': '25.00',
            'cluster': 1,
            'elapsed_str': '0min 25sec',
            'num_hosts': 2,
            'time_taken_manually_execute_minutes': 60,
            'time_taken_create_automation_minutes': 60,
            'successful_runs': 1,
            'failed_runs': 0,
            'automated_costs': '8.33',
            'manual_costs': '6000.00',
            'savings': '5991.67',
            'job_template_id': 2,
            'time_savings': '7175.00',
            'time_savings_str': '1h 59min 35sec'
        }
    ]
}

test_template_expected_data = {
    'count': 3,
    'next': None,
    'previous': None,
    'results': [
        {'key': 1, 'value': 'Job Template A', 'cluster_id': 1},
        {'key': 2, 'value': 'Job Template B', 'cluster_id': 1},
        {'key': 3, 'value': 'Job Template C', 'cluster_id': 1}
    ]
}

test_labels_expected_data = {
    'count': 3,
    'next': None,
    'previous': None,
    'results': [
        {'key': 1, 'value': 'Label A', 'cluster_id': 1},
        {'key': 2, 'value': 'Label B', 'cluster_id': 1},
        {'key': 3, 'value': 'Label C', 'cluster_id': 1}
    ]
}

test_organizations_expected_data = {
    'count': 2,
    'next': None,
    'previous': None,
    'results': [
        {'key': 2, 'value': 'Organization A', 'cluster_id': 1},
        {'key': 1, 'value': 'Organization B', 'cluster_id': 1}
    ]
}

test_projects_expected_data = {
    'count': 3,
    'next': None,
    'previous': None,
    'results': [
        {'key': 1, 'value': 'Project A', 'cluster_id': 1},
        {'key': 2, 'value': 'Project B', 'cluster_id': 1},
        {'key': 3, 'value': 'Project C', 'cluster_id': 1},
    ]
}

ENDPOINTS = {
    "get": [
        "/api/v1/common/currencies/",
        "/api/v1/common/settings/",
        "/api/v1/template_options/",
        "/api/v1/report/?page=1&page_size=10&date_range=month_to_date",
        "/api/v1/report/details/?page=1&page_size=10&date_range=year_to_date",
        "/api/v1/report/csv/?date_range=last_month",
        "/api/v1/templates/?page=1&page_size=10",
        "/api/v1/labels/?page=1&page_size=10",
        "/api/v1/projects/?page=1&page_size=10",
        "/api/v1/organizations/?page=1&page_size=10",
        "/api/v1/metrics/",
    ],
    "post": [
        "/api/v1/costs/",
        "/api/v1/common/filter_set/",
        "/api/v1/common/settings/",
        "/api/v1/common/settings/",
        "/api/v1/report/pdf/?date_range=last_month",
        "/api/v1/template_options/restore_user_inputs/"
    ],
    "put": [
        "/api/v1/templates/1/",
        "/api/v1/common/filter_set/1/",
    ],
    "delete": [
        "/api/v1/common/filter_set/1/"
    ],
}


@pytest.fixture(scope="function")
def mock_auth(superuser):
    with mock.patch("backend.apps.aap_auth.authentication.AAPAuthentication.authenticate") as mock_authenticate:
        mock_authenticate.return_value = superuser, None
        yield mock_authenticate


@pytest.fixture(scope="function")
def mock_auth_user(regularuser):
    with mock.patch("backend.apps.aap_auth.authentication.AAPAuthentication.authenticate") as mock_authenticate:
        mock_authenticate.return_value = regularuser, None
        yield mock_authenticate


@pytest.fixture(scope="function")
def mock_auth_user(regularuser):
    with mock.patch("backend.apps.aap_auth.authentication.AAPAuthentication.authenticate") as mock_authenticate:
        mock_authenticate.return_value = regularuser, None
        yield mock_authenticate


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestViews:

    def test_ping(self, mocker):
        view = PingView()
        ret = view.get(mocker.MagicMock())
        assert ret.status_code == 200

    @pytest.mark.parametrize('expected', [
        [
            {'id': 2, 'name': 'EUR', 'iso_code': 'EUR', 'symbol': '€'},
            {'id': 1, 'name': 'United States Dollar', 'iso_code': 'USD', 'symbol': '$'}
        ]
    ])
    def test_currency(self, mock_auth, currencies, expected):
        client = APIClient()
        response = client.get('/api/v1/common/currencies/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data == expected

    @pytest.mark.parametrize('expected', [test_template_option_expected_data])
    def test_template_options(self, mock_auth, currencies, projects, jobs, filter_sets, labels, expected):
        client = APIClient()
        response = client.get("/api/v1/template_options/")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    @pytest.mark.parametrize('expected', [test_report_expected_data])
    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_report(self, mock_auth, host_summaries, projects, expected):
        client = APIClient()
        response = client.get('/api/v1/report/?page=1&page_size=10&date_range=month_to_date')
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    @pytest.mark.parametrize('expected', [test_report_past_month_expected_data])
    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_report_past_month(self, mock_auth, host_summaries, projects, expected):
        client = APIClient()
        response = client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    @pytest.mark.parametrize('expected', [
        {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }
    ])
    @time_machine.travel(datetime(2025, 12, 31, 22, 1, 45, tzinfo=pytz.UTC))
    def test_report_by_project(self, mock_auth, host_summaries, projects, expected):
        client = APIClient()
        project = Project.objects.get(name="Project B")
        response = client.get(f"/api/v1/report/?page=1&page_size=10&date_range=year_to_date&project={project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

        project = Project.objects.get(name="Project A")
        response = client.get(f"/api/v1/report/?page=1&page_size=10&date_range=year_to_date&project={project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    @pytest.mark.parametrize('expected', [test_report_details_expected_data])
    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_report_details(self, mock_auth, host_summaries, projects, expected):
        client = APIClient()
        response = client.get("/api/v1/report/details/?page=1&page_size=10&date_range=year_to_date")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    def test_update_template_manual_time(self, mock_auth, job_templates):
        client = APIClient()
        job_template = JobTemplate.objects.get(name="Job Template A")
        data = dict(time_taken_manually_execute_minutes=120, time_taken_create_automation_minutes=30)
        response = client.put(f"/api/v1/templates/{job_template.id}/", content_type='application/json',
                              data=json.dumps(data))
        assert response.status_code == 200
        job_template = JobTemplate.objects.get(name="Job Template A")
        assert job_template.time_taken_manually_execute_minutes == 120
        assert job_template.time_taken_create_automation_minutes == 30

    def test_update_manual_costs(self, mock_auth):
        client = APIClient()
        data = dict(type="manual", value=1000)
        response = client.post(f"/api/v1/costs/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 202
        costs = Costs.get()
        assert costs[CostsChoices.MANUAL] == 1000

    def test_update_automated_costs(self, mock_auth):
        client = APIClient()
        data = dict(type="automated", value=1000)
        response = client.post(f"/api/v1/costs/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 202
        costs = Costs.get()
        assert costs[CostsChoices.AUTOMATED] == 1000

    def test_create_new_report(self, mock_auth):
        client = APIClient()
        data = dict(name="Report 3", filters=dict(date_range='last_month'))
        response = client.post("/api/v1/common/filter_set/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 201
        filter_set = FilterSet.objects.get(name="Report 3")
        assert filter_set.name == "Report 3"
        assert filter_set.filters == dict(date_range='last_month')

    def test_create_new_report_same_name(self, mock_auth, filter_sets):
        data = dict(name="Report 1", filters=dict(date_range='last_month'))
        client = APIClient()
        response = client.post("/api/v1/common/filter_set/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 400
        data = response.json()
        assert data == {'name': ['Filter name already exists.']}

    def test_update_report(self, mock_auth, filter_sets):
        client = APIClient()
        filter_set = FilterSet.objects.get(name="Report 1")
        data = dict(name="Report 1 updated", filters=dict(date_range='last_year'))
        response = client.put(f"/api/v1/common/filter_set/{filter_set.id}/", content_type='application/json',
                              data=json.dumps(data))
        assert response.status_code == 200
        filter_set = FilterSet.objects.get(name="Report 1 updated")
        assert filter_set.filters == dict(date_range='last_year')

    def test_delete_report(self, mock_auth, filter_sets):
        client = APIClient()
        filter_set = FilterSet.objects.get(name="Report 1")
        response = client.delete(f"/api/v1/common/filter_set/{filter_set.id}/")
        assert response.status_code == 204
        with pytest.raises(FilterSet.DoesNotExist):
            FilterSet.objects.get(name="Report 1")

    def test_change_currency(self, mock_auth, currencies):
        client = APIClient()
        us_currency = Currency.objects.get(iso_code="USD")
        template_response = client.get("/api/v1/template_options/")
        assert template_response.status_code == 200
        template_data = template_response.json()
        assert template_data["currency"] == us_currency.id
        currency = Currency.objects.get(iso_code="EUR")
        data = dict(type="currency", value=currency.id)

        response = client.post(f"/api/v1/common/settings/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 201

        template_response = client.get("/api/v1/template_options/")
        assert template_response.status_code == 200
        template_data = template_response.json()
        assert template_data["currency"] == currency.id

    def test_disable_time_taken_to_create_automation_save(self, mock_auth):
        client = APIClient()
        data = dict(type="enable_template_creation_time", value=False)
        response = client.post(f"/api/v1/common/settings/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 201
        db_data = Settings.objects.get(type=SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME)
        assert db_data.value == 0

    @pytest.mark.parametrize('expected', [test_report_disabled_time_taken_to_create_automation_save_expected_data])
    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_report_disabled_time_taken_to_create_automation_save(self, mock_auth, host_summaries, projects, expected):
        client = APIClient()
        data = dict(type="enable_template_creation_time", value=False)
        response = client.post(f"/api/v1/common/settings/", content_type='application/json', data=json.dumps(data))
        assert response.status_code == 201
        response = client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_export_csv(self, mock_auth, host_summaries, projects):
        client = APIClient()
        response = client.get("/api/v1/report/csv/?date_range=last_month")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        cvs_reader = csv.reader(io.StringIO(content))
        body = list(cvs_reader)
        headers = body.pop(0)
        assert len(body[0]) == 10
        assert len(headers) == 10
        expected_data = [
            ("Name", "Job Template B"),
            ("Number of job executions", "1"),
            ("Hosts executions", "2"),
            ("Time taken to manually execute (minutes)", "60"),
            ("Time taken to create automation (minutes)", "60"),
            ("Running time (seconds)", "25.000"),
            ("Running time", "0min 25sec"),
            ("Automated costs", "3008.33"),
            ("Manual costs", "6000.00"),
            ("Savings", "2991.67"),
        ]

        for index, data in enumerate(expected_data):
            assert headers[index] == data[0]
            assert body[0][index] == data[1]

    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_export_pdf(self, mock_auth, host_summaries, projects, currencies):
        client = APIClient()
        response = client.post("/api/v1/report/pdf/?date_range=last_month")
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "endpoint, fixture_name, expected",
        [
            ("/api/v1/templates/?page=1&page_size=10", "job_templates", test_template_expected_data),
            ("/api/v1/labels/?page=1&page_size=10", "labels", test_labels_expected_data),
            ("/api/v1/organizations/?page=1&page_size=10", "organizations", test_organizations_expected_data),
            ("/api/v1/projects/?page=1&page_size=10", "projects", test_projects_expected_data),
        ]
    )
    def test_filters_list_endpoints(self, request, mock_auth, endpoint, fixture_name, expected):
        request.getfixturevalue(fixture_name)
        client = APIClient()
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    @pytest.mark.parametrize('expected', [test_projects_expected_data])
    def test_projects(self, mock_auth, projects, expected):
        client = APIClient()
        response = client.get(f"/api/v1/projects/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data == expected

    def test_not_authenticated(self, filter_sets, job_templates):
        client = APIClient()
        for url in ENDPOINTS["get"]:
            response = client.get(url)
            assert response.status_code == 401

        for url in ENDPOINTS["post"]:
            response = client.post(url)
            assert response.status_code == 401

        for url in ENDPOINTS["put"]:
            response = client.put(url)
            assert response.status_code == 401

        for url in ENDPOINTS["delete"]:
            response = client.delete(url)
            assert response.status_code == 401

    def test_insufficient_permissions(self, mock_auth_user, filter_sets, job_templates):
        client = APIClient()
        for url in ENDPOINTS["get"]:
            response = client.get(url)
            assert response.status_code == 403

        for url in ENDPOINTS["post"]:
            response = client.post(url)
            assert response.status_code == 403

        for url in ENDPOINTS["put"]:
            response = client.put(url)
            assert response.status_code == 403

        for url in ENDPOINTS["delete"]:
            response = client.delete(url)
            assert response.status_code == 403

    @time_machine.travel(datetime(2025, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_restore_user_inputs(self, mock_auth, host_summaries, projects):
        client = APIClient()
        response = client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        response_data = response.json()
        assert response_data["results"][0]["time_taken_manually_execute_minutes"] == 60
        post_response = client.post("/api/v1/template_options/restore_user_inputs/")
        assert post_response.status_code == 204
        response = client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        response_data = response.json()
        assert response_data["results"][0]["time_taken_manually_execute_minutes"] == 1
