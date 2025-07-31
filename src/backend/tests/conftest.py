import datetime

import pytest
import pytz
from django.core.cache import cache

from backend.apps.clusters.models import Cluster, Organization, Label, JobTemplate, Project, Job, JobTypeChoices, JobLaunchTypeChoices, InstanceGroup, ExecutionEnvironment, Inventory, AAPUser, JobStatusChoices, Host, JobHostSummary
from backend.apps.common.models import Currency, FilterSet


def pytest_addoption(parser):
    parser.addoption("--genschema", action="store_true", default=False, help="execute schema validator")


def pytest_configure(config):
    import sys

    sys._called_from_test = True

def pytest_unconfigure(config):
    import sys

    del sys._called_from_test


def pytest_runtest_teardown(item, nextitem):
    # clear Django cache at the end of every test ran
    # NOTE: this should not be memcache (as it is deprecated), nor should it be redis.
    # This is a local test cache, so we want every test to start with an empty cache
    cache.clear()


@pytest.fixture
def currencies():
    currencies = [
        Currency(name="United states dollar", iso_code="USD", symbol="$"),
        Currency(name="EUR", iso_code="EUR", symbol="€")
    ]
    return Currency.objects.bulk_create(currencies)


@pytest.fixture
def cluster():
    return Cluster.objects.create(
        protocol="https",
        address="localhost",
        port=8000,
        access_token="<PASSWORD>",
        verify_ssl=False)


@pytest.fixture
def organizations(cluster):
    orgs = [
        Organization(name="Organization B", cluster=cluster, external_id=1),
        Organization(name="Organization A", cluster=cluster, external_id=2),
    ]
    return Organization.objects.bulk_create(orgs)


@pytest.fixture
def labels(cluster):
    labels = [
        Label(name="Label A", cluster=cluster, external_id=1),
        Label(name="Label B", cluster=cluster, external_id=2),
        Label(name="Label C", cluster=cluster, external_id=3),
    ]
    return Label.objects.bulk_create(labels)


@pytest.fixture
def job_templates(cluster):
    templates = [
        JobTemplate(name="Job Template A", cluster=cluster, external_id=1),
        JobTemplate(name="Job Template B", cluster=cluster, external_id=2),
        JobTemplate(name="Job Template C", cluster=cluster, external_id=4),
    ]
    return JobTemplate.objects.bulk_create(templates)


@pytest.fixture
def projects(cluster):
    projects = [
        Project(name="Project A", cluster=cluster, external_id=1),
        Project(name="Project B", cluster=cluster, external_id=2),
    ]
    return Project.objects.bulk_create(projects)


@pytest.fixture
def instance_group(cluster):
    return InstanceGroup.objects.create(name="Instance Group A", cluster=cluster, external_id=1)


@pytest.fixture
def execution_environment(cluster):
    return ExecutionEnvironment.objects.create(name="Execution Environment", cluster=cluster, external_id=1)


@pytest.fixture
def inventory(cluster):
    return Inventory.objects.create(name="Inventory A", cluster=cluster, external_id=1)


@pytest.fixture
def aap_user(cluster):
    return AAPUser.objects.create(name="AAP User", cluster=cluster, external_id=1, type="user")


@pytest.fixture
def jobs(

        cluster,
        organizations,
        job_templates,
        instance_group,
        execution_environment,
        inventory,
        aap_user,
        projects
):
    jobs = [
        Job(
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
            started=datetime.datetime.strptime('2025-03-01T10:00:00Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            finished=datetime.datetime.strptime('2025-03-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            elapsed=25,
            failed=False,
            num_hosts=2,
            project=Project.objects.get(name="Project A"),
            cluster=cluster,
            external_id=1),

        Job(
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
            started=datetime.datetime.strptime('2025-02-01T10:00:00Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            finished=datetime.datetime.strptime('2025-02-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC')),
            elapsed=25,
            failed=False,
            num_hosts=2,
            project=Project.objects.get(name="Project A"),
            cluster=cluster,
            external_id=1)
    ]
    return Job.objects.bulk_create(jobs)


@pytest.fixture
def filter_sets():
    filters = [
        FilterSet.objects.create(name="Report 1", filters=dict(date_range='last_month', organization=[1, 2])),
        FilterSet.objects.create(name="Report 2", filters=dict(date_range='last_year', template=[1, 2])),
    ]
    return filters


@pytest.fixture
def hosts(cluster):
    hosts = [
        Host(name="Host A", cluster=cluster, external_id=1),
        Host(name="Host B", cluster=cluster, external_id=2),
        Host(name="Host C", cluster=cluster, external_id=3),
    ]
    return Host.objects.bulk_create(hosts)


@pytest.fixture
def host_summaries(jobs, hosts):
    created = datetime.datetime.strptime('2025-03-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC'))
    created2 = datetime.datetime.strptime('2025-02-01T10:00:25Z', '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('UTC'))
    job1 = Job.objects.get(name="Job Template A")
    job2 = Job.objects.get(name="Job Template B")
    host_1 = Host.objects.get(name="Host A")
    host_2 = Host.objects.get(name="Host B")
    host_3 = Host.objects.get(name="Host C")
    summaries = [
        JobHostSummary(
            job=job1,
            host=host_1,
            host_name=host_1.name,
            created=created,
            modified=created

        ),
        JobHostSummary(
            job=job1,
            host=host_2,
            host_name=host_2.name,
            created=created,
            modified=created
        ),
        JobHostSummary(
            job=job2,
            host=host_1,
            host_name=host_1.name,
            created=created2,
            modified=created2
        ),
        JobHostSummary(
            job=job2,
            host=host_2,
            host_name=host_2.name,
            created=created2,
            modified=created2
        ),
        JobHostSummary(
            job=job2,
            host=host_3,
            host_name=host_3.name,
            created=created2,
            modified=created2
        )
    ]

    return JobHostSummary.objects.bulk_create(summaries)
