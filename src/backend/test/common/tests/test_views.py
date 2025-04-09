#! /usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import io
from datetime import datetime
from decimal import Decimal

import pytest
import pytz
from django.test import TestCase
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from rest_framework import status
from rest_framework.reverse import reverse

from backend.apps.clusters.helpers import get_costs
from backend.apps.clusters.models import (
    Cluster,
    Organization,
    Label,
    JobTemplate,
    Job,
    JobTypeChoices,
    JobLaunchTypeChoices,
    InstanceGroup,
    ExecutionEnvironment,
    Inventory,
    AAPUser,
    JobStatusChoices,
    Project,
    JobHostSummary,
    Host,
    CostsChoices)
from backend.apps.common.models import FilterSet, Currency, Settings, SettingsChoices


@pytest.mark.django_db()
class TestViews(TestCase):
    setup_done = False

    @classmethod
    def setUpTestData(cls):
        cluster = Cluster.objects.create(protocol="https", address="localhost", port=8000, access_token="<PASSWORD>", verify_ssl=False)
        Organization.objects.create(name="Organization B", cluster=cluster, external_id=1)
        Organization.objects.create(name="Organization A", cluster=cluster, external_id=2)
        Label.objects.create(name="Label A", cluster=cluster, external_id=1)
        Label.objects.create(name="Label C", cluster=cluster, external_id=2)
        Label.objects.create(name="Label B", cluster=cluster, external_id=3)
        JobTemplate.objects.create(name="Job Template A", cluster=cluster, external_id=1)
        JobTemplate.objects.create(name="Job Template B", cluster=cluster, external_id=1)
        JobTemplate.objects.create(name="Job Template C", cluster=cluster, external_id=1)

        InstanceGroup.objects.create(name="Instance Group A", cluster=cluster, external_id=1)
        ExecutionEnvironment.objects.create(name="Execution Environment", cluster=cluster, external_id=1)
        Inventory.objects.create(name="Inventory A", cluster=cluster, external_id=1)

        AAPUser.objects.create(name="AAP User", cluster=cluster, external_id=1, type="user")
        Project.objects.create(name="Project A", cluster=cluster, external_id=1)
        Project.objects.create(name="Project B", cluster=cluster, external_id=2)

        host_1 = Host.objects.create(name="Host A", cluster=cluster, external_id=1)
        host_2 = Host.objects.create(name="Host B", cluster=cluster, external_id=2)
        host_3 = Host.objects.create(name="Host C", cluster=cluster, external_id=3)

        job1 = Job.objects.create(
            type=JobTypeChoices.JOB,
            launch_type=JobLaunchTypeChoices.MANUAL,
            name="Job Template A",
            description="",
            organization=Organization.objects.get(name="Organization A"),
            instance_group=InstanceGroup.objects.get(name="Instance Group A"),
            execution_environment=ExecutionEnvironment.objects.get(name="Execution Environment"),
            inventory=Inventory.objects.get(name="Inventory A"),
            job_template=JobTemplate.objects.get(name="Job Template A"),
            launched_by=AAPUser.objects.get(name="AAP User"),
            status=JobStatusChoices.SUCCESSFUL,
            started=datetime.strptime('2025-03-01T10:00:00Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            finished=datetime.strptime('2025-03-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            elapsed=25,
            failed=False,
            num_hosts=2,
            project=Project.objects.get(name="Project A"),
            cluster=cluster,
            external_id=1)

        job2 = Job.objects.create(
            type=JobTypeChoices.JOB,
            launch_type=JobLaunchTypeChoices.MANUAL,
            name="Job Template B",
            description="",
            organization=Organization.objects.get(name="Organization A"),
            instance_group=InstanceGroup.objects.get(name="Instance Group A"),
            execution_environment=ExecutionEnvironment.objects.get(name="Execution Environment"),
            inventory=Inventory.objects.get(name="Inventory A"),
            job_template=JobTemplate.objects.get(name="Job Template B"),
            launched_by=AAPUser.objects.get(name="AAP User"),
            status=JobStatusChoices.SUCCESSFUL,
            started=datetime.strptime('2025-02-01T10:00:00Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            finished=datetime.strptime('2025-02-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            elapsed=25,
            failed=False,
            num_hosts=2,
            project=Project.objects.get(name="Project A"),
            cluster=cluster,
            external_id=1)

        created = datetime.strptime('2025-03-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC'))

        JobHostSummary.objects.create(
            job=job1,
            host=host_1,
            host_name=host_1.name,
            created=created,
            modified=created

        )

        JobHostSummary.objects.create(
            job=job1,
            host=host_2,
            host_name=host_2.name,
            created=created,
            modified=created
        )

        created = datetime.strptime('2025-02-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC'))

        JobHostSummary.objects.create(
            job=job2,
            host=host_1,
            host_name=host_1.name,
            created=created,
            modified=created
        )
        JobHostSummary.objects.create(
            job=job2,
            host=host_2,
            host_name=host_2.name,
            created=created,
            modified=created
        )
        JobHostSummary.objects.create(
            job=job2,
            host=host_3,
            host_name=host_3.name,
            created=created,
            modified=created
        )

        FilterSet.objects.create(
            name="Report 1",
            filters=dict(
                date_range='last_month',
                organization=[1, 2]
            ),
        )
        FilterSet.objects.create(
            name="Report 2",
            filters=dict(
                date_range='last_year',
                template=[1, 2]
            ),
        )

    def test_ping(self):
        response = self.client.get(f"{reverse('ping')}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            dict(data),
            dict(
                ping="pong",
                clusters=[
                    dict(id=1, address="localhost")
                ]
            )
        )

    def test_template_options(self):
        response = self.client.get(f"{reverse('template_options')}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            dict(response.data),
            dict(
                clusters=[
                    dict(id=1, address='localhost')
                ],
                organizations=[
                    dict(key=2, value='Organization A', cluster_id=1),
                ],
                labels=[
                    dict(key=1, value='Label A', cluster_id=1),
                    dict(key=3, value='Label B', cluster_id=1),
                    dict(key=2, value='Label C', cluster_id=1),
                ],
                date_ranges=[
                    dict(key='last_year', value='Past year'),
                    dict(key='last_6_month', value='Past 6 months'),
                    dict(key='last_3_month', value='Past 3 months'),
                    dict(key='last_month', value='Past month'),
                    dict(key='year_to_date', value='Year to date'),
                    dict(key='quarter_to_date', value='Quarter to date'),
                    dict(key='month_to_date', value='Month to date'),
                    dict(key='last_3_years', value='Past 3 years'),
                    dict(key='last_2_years', value='Past 2 years'),
                    dict(key='custom', value='Custom'),
                ],
                job_templates=[
                    dict(key=1, value='Job Template A', cluster_id=1),
                    dict(key=2, value='Job Template B', cluster_id=1),
                ],
                projects=[
                    dict(key=1, value='Project A', cluster_id=1),
                    dict(key=2, value='Project B', cluster_id=1)
                ],
                manual_cost_automation=Decimal('50.00'),
                automated_process_cost=Decimal('20.00'),
                currencies=[
                    dict(id=3, name='British Pound Sterling', iso_code='GBP', symbol='£'),
                    dict(id=5, name='Chinese Yuan Renminbi', iso_code='CNY', symbol='¥'),
                    dict(id=2, name='Euro', iso_code='EUR', symbol='€'),
                    dict(id=4, name='Japanese yen', iso_code='JPY', symbol='¥'),
                    dict(id=1, name='United States dollar', iso_code='USD', symbol='$'),
                ],
                currency=1,
                enable_template_creation_time=True,
                filter_sets=[
                    dict(id=1, name='Report 1', filters=dict(date_range='last_month', organization=[1, 2])),
                    dict(id=2, name='Report 2', filters=dict(date_range='last_year', template=[1, 2])),
                ],
            )
        )

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_report(self):
        response = self.client.get("/api/v1/report/?page=1&page_size=10&date_range=month_to_date")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            dict(data),
            dict(
                count=1,
                next=None,
                previous=None,
                results=[
                    dict(
                        name='Job Template A',
                        runs=1,
                        elapsed='25.00',
                        cluster=1,
                        elapsed_str='0min 25sec',
                        num_hosts=2,
                        time_taken_manually_execute_minutes=60,
                        time_taken_create_automation_minutes=60,
                        successful_runs=1,
                        failed_runs=0,
                        automated_costs='3008.33',
                        manual_costs='6000.00',
                        savings='2991.67',
                        job_template_id=1,
                        time_savings='10775.00',
                        time_savings_str='2h 59min 35sec'
                    )
                ]
            )
        )

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_report_past_month(self):
        response = self.client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            dict(data),
            dict(
                count=1,
                next=None,
                previous=None,
                results=[
                    dict(
                        name='Job Template B',
                        runs=1,
                        elapsed='25.00',
                        cluster=1,
                        elapsed_str='0min 25sec',
                        num_hosts=2,
                        time_taken_manually_execute_minutes=60,
                        time_taken_create_automation_minutes=60,
                        successful_runs=1,
                        failed_runs=0,
                        automated_costs='3008.33',
                        manual_costs='6000.00',
                        savings='2991.67',
                        job_template_id=2,
                        time_savings='10775.00',
                        time_savings_str='2h 59min 35sec',
                    )
                ]
            )
        )

    @freeze_time("2025-12-31 22:01:45", tz_offset=0)
    def test_report_by_project(self):
        project = Project.objects.get(name="Project B")
        response = self.client.get(f"/api/v1/report/?page=1&page_size=10&date_range=year_to_date&project={project.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            dict(data),
            dict(
                count=0,
                next=None,
                previous=None,
                results=[]
            )
        )
        project = Project.objects.get(name="Project A")
        response = self.client.get(f"/api/v1/report/?page=1&page_size=10&date_range=year_to_date&project={project.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            data["count"], 2
        )

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_report_details(self):
        response = self.client.get("/api/v1/report/details/?page=1&page_size=10&date_range=year_to_date")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(
            dict(data),
            dict(
                users=[dict(user_id=1, user_name='AAP User', count=2)],
                projects=[dict(project_id=1, project_name='Project A', count=2)],
                total_number_of_unique_hosts=dict(value=3),
                total_number_of_successful_jobs=dict(value=2),
                total_number_of_failed_jobs=dict(value=0),
                total_number_of_job_runs=dict(value=2),
                total_number_of_host_job_runs=dict(value=4),
                total_hours_of_automation=dict(value=Decimal('0.01')),
                cost_of_automated_execution=dict(value=Decimal('6016.67')),
                cost_of_manual_automation=dict(value=Decimal('12000.00')),
                total_saving=dict(value=Decimal('5983.33')),
                total_time_saving=dict(value=Decimal('5.99')),
                excluded_templates=[
                    dict(id=3, name='Job Template C'),
                ],
                host_chart=dict(
                    items=[
                        dict(x=FakeDatetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC), y=0),
                        dict(x=FakeDatetime(2025, 2, 1, 0, 0, tzinfo=pytz.UTC), y=2),
                        dict(x=FakeDatetime(2025, 3, 1, 0, 0, tzinfo=pytz.UTC), y=2),
                    ],
                    range='month'),
                job_chart=dict(
                    items=[
                        dict(x=FakeDatetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC), y=0),
                        dict(x=FakeDatetime(2025, 2, 1, 0, 0, tzinfo=pytz.UTC), y=1),
                        dict(x=FakeDatetime(2025, 3, 1, 0, 0, tzinfo=pytz.UTC), y=1),
                    ],
                    range='month'),
                related_links=dict(
                    successful_jobs='https://localhost:8000#/jobs?job.finished__gte=2025-01-01T00%3A00%3A00%2B00%3A00&job.finished__lte=2025-03-21T23%3A59%3A59.999999%2B00%3A00&job.status__exact=successful',
                    failed_jobs='https://localhost:8000#/jobs?job.status__exact=failed&job.finished__gte=2025-01-01T00%3A00%3A00%2B00%3A00&job.finished__lte=2025-03-21T23%3A59%3A59.999999%2B00%3A00'
                )
            )
        )

    def test_update_template_manual_time(self):
        job_template = JobTemplate.objects.get(name="Job Template A")
        data = dict(time_taken_manually_execute_minutes=120, time_taken_create_automation_minutes=30)
        response = self.client.put(f"/api/v1/templates/{job_template.id}/", content_type='application/json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_template = JobTemplate.objects.get(name="Job Template A")
        self.assertEqual(job_template.time_taken_manually_execute_minutes, 120)
        self.assertEqual(job_template.time_taken_create_automation_minutes, 30)

    def test_update_manual_costs(self):
        response = self.client.post(f"/api/v1/costs/", content_type='application/json', data=dict(type="manual", value=1000))
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        costs = get_costs()
        self.assertEqual(costs[CostsChoices.MANUAL].value, 1000)

    def test_update_automated_costs(self):
        response = self.client.post(f"/api/v1/costs/", content_type='application/json', data=dict(type="automated", value=1000))
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        costs = get_costs()
        self.assertEqual(costs[CostsChoices.AUTOMATED].value, 1000)

    def test_create_new_report(self):
        response = self.client.post(f"/api/v1/common/filter_set/", content_type='application/json', data=dict(name="Report 3", filters=dict(date_range='last_month')))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        filter_set = FilterSet.objects.get(name="Report 3")
        self.assertEqual(filter_set.filters, dict(date_range='last_month'))

    def test_create_new_report_same_name(self):
        response = self.client.post(f"/api/v1/common/filter_set/", content_type='application/json', data=dict(name="Report 1", filters=dict(date_range='last_month')))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"name": ["Filter name already exists."]})

    def test_update_report(self):
        filter_set = FilterSet.objects.get(name="Report 1")
        response = self.client.put(f"/api/v1/common/filter_set/{filter_set.id}/", content_type='application/json', data=dict(name="Report 1 updated", filters=dict(date_range='last_month')))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        filter_set = FilterSet.objects.get(name="Report 1 updated")
        self.assertEqual(filter_set.filters, dict(date_range='last_month'))

    def test_delete_report(self):
        filter_set = FilterSet.objects.get(name="Report 1")
        response = self.client.delete(f"/api/v1/common/filter_set/{filter_set.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(FilterSet.DoesNotExist):
            FilterSet.objects.get(name="Report 1")

    def test_change_currency(self):
        currency = Currency.objects.get(iso_code="EUR")
        response = self.client.post(f"/api/v1/common/settings/", content_type='application/json', data=dict(type="currency", value=currency.id))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        template_response = self.client.get(f"{reverse('template_options')}")
        self.assertEqual(template_response.status_code, status.HTTP_200_OK)
        template_dict = dict(template_response.data)
        self.assertEqual(template_dict['currency'], currency.id)

    def test_disable_time_taken_to_create_automation_save(self):
        response = self.client.post(f"/api/v1/common/settings/", content_type='application/json', data=dict(type="enable_template_creation_time", value=False))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = Settings.objects.get(type=SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME)
        self.assertEqual(data.value, 0)

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_report_disabled_time_taken_to_create_automation_save(self):
        response = self.client.post(f"/api/v1/common/settings/", content_type='application/json', data=dict(type="enable_template_creation_time", value=False))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get("/api/v1/report/?page=1&page_size=10&date_range=last_month")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data["results"]), 1)
        result = data["results"][0]
        self.assertEqual(result["automated_costs"], "8.33")
        self.assertEqual(result["manual_costs"], "6000.00")
        self.assertEqual(result["savings"], "5991.67"),
        self.assertEqual(result["time_savings"], "7175.00")
        self.assertEqual(result["time_savings_str"], "1h 59min 35sec")

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_export_csv(self):
        response = self.client.get("/api/v1/report/csv/?date_range=last_month")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        cvs_reader = csv.reader(io.StringIO(content))

        body = list(cvs_reader)
        headers = body.pop(0)

        self.assertEqual(len(body[0]), 10)
        self.assertEqual(len(headers), 10)
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
            self.assertEqual(headers[index], data[0], msg=headers[index])
            self.assertEqual(body[0][index], data[1], msg=headers[index])

    @freeze_time("2025-03-21 22:01:45", tz_offset=0)
    def test_export_pdf(self):
        response = self.client.post("/api/v1/report/pdf/?date_range=last_month")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
