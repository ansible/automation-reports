from datetime import datetime
from decimal import Decimal

import pytest
import pytz

from backend.apps.clusters.models import (
    Organization,
    JobTemplate,
    AAPUser,
    Inventory,
    ExecutionEnvironment,
    InstanceGroup,
    Label,
    Project,
    Host,
    Job,
    JobHostSummary)
from backend.apps.clusters.parser import DataParser
from backend.apps.clusters.schemas import ExternalJobSchema, NameDescriptionModelSchema, LabelModelSchema

org_expected_data = {
    "name": "Organization A",
    "external_id": 2,
    "description": "Description for organization A",
    "cluster_id": 1
}

job_template_expected_data = {
    "name": "Job Template B",
    "description": "Description for job template B",
    "external_id": 2,
    "cluster_id": 1,
    "time_taken_manually_execute_minutes": 60,
    "time_taken_create_automation_minutes": 60,

}

aap_user_expected_data = {
    "name": "AAP User",
    "external_id": 1,
    "type": "user",
    "cluster_id": 1
}

inventory_expected_data = {
    "name": "Inventory A",
    "description": "Description for inventory A",
    "external_id": 1,
    "cluster_id": 1
}

ee_expected_data = {
    "name": "Execution Environment",
    "description": "Execution Environment description",
    "external_id": 1,
    "cluster_id": 1
}

instance_group_expected_data = {
    "name": "Instance Group A",
    "is_container_group": False,
    "external_id": 1,
    "cluster_id": 1,
}

project_expected_data = {
    "name": "Project B",
    "description": "Project B description",
    "scm_type": "",
    "external_id": 2,
    "cluster_id": 1
}

host_expected_data = {
    "name": "Host C",
    "description": "Host C description",
    "external_id": 3,
    "cluster_id": 1
}

host_summaries_expected_data = [
    {
        'host_name': 'Host B',
        'changed': 0,
        'dark': 0,
        'failures': 0,
        'ok': 2,
        'processed': 1,
        'skipped': 0,
        'failed': False,
        'ignored': 0,
        'rescued': 0,
        'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
        'modified': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc)
    },
    {
        'host_name': 'Host C',
        'changed': 0,
        'dark': 0,
        'failures': 0,
        'ok': 4,
        'processed': 1,
        'skipped': 0,
        'failed': False,
        'ignored': 0,
        'rescued': 0,
        'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
        'modified': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc)
    }
]

job_expected_data = {
    'id': 2,
    'name': 'Job Template B',
    'description': '',
    'started': datetime(2025, 4, 5, 18, 30, 3, 963413, tzinfo=pytz.utc),
    'finished': datetime(2025, 4, 5, 18, 30, 12, 226281, tzinfo=pytz.utc),
    'elapsed': Decimal('8.263'),
    'failed': False,
    'status': 'successful',
    'job_type': 'run',
    'type': 'job',
    'launch_type': 'manual',
    'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
    'modified': datetime(2025, 4, 5, 18, 30, 3, 739997, tzinfo=pytz.utc)
}

parsed_job_expected_data = {
    'job': {
        'id': 1,
        'cluster_id': 1,
        'external_id': 2,
        'type': 'job',
        'job_type': 'run',
        'launch_type': 'manual',
        'name': 'Job Template B',
        'description': '',
        'organization_id': 1,
        'instance_group_id': 1,
        'execution_environment_id': 1,
        'inventory_id': 1,
        'job_template_id': 1,
        'launched_by_id': 1,
        'status': 'successful',
        'started': datetime(2025, 4, 5, 18, 30, 3, 963413, tzinfo=pytz.utc),
        'finished': datetime(2025, 4, 5, 18, 30, 12, 226281, tzinfo=pytz.utc),
        'elapsed': Decimal('8.263'),
        'failed': False,
        'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
        'modified': datetime(2025, 4, 5, 18, 30, 3, 739997, tzinfo=pytz.utc),
        'num_hosts': 2,
        'changed_hosts_count': 0,
        'dark_hosts_count': 0,
        'failures_hosts_count': 0,
        'ok_hosts_count': 6,
        'processed_hosts_count': 2,
        'skipped_hosts_count': 0,
        'failed_hosts_count': 0,
        'ignored_hosts_count': 0,
        'rescued_hosts_count': 0,
        'project_id': 1
    },
    "host_summaries": [
        {
            'id': 1,
            'job_id': 1,
            'host_id': 1,
            'host_name': 'Host B',
            'changed': 0,
            'dark': 0,
            'failures': 0,
            'ok': 2,
            'processed': 1,
            'skipped': 0,
            'failed': False,
            'ignored': 0,
            'rescued': 0,
            'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
            'modified': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc)
        },
        {
            'id': 2,
            'job_id': 1,
            'host_id': 2,
            'host_name': 'Host C',
            'changed': 0,
            'dark': 0,
            'failures': 0,
            'ok': 4,
            'processed': 1,
            'skipped': 0,
            'failed': False,
            'ignored': 0,
            'rescued': 0,
            'created': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc),
            'modified': datetime(2025, 4, 5, 18, 30, 2, 851402, tzinfo=pytz.utc)
        }
    ]

}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestParser:

    def test_init(self, cluster, cluster_sync_data):
        parser = DataParser(cluster_sync_data.id)
        assert parser.cluster == cluster
        assert parser.data == ExternalJobSchema(**cluster_sync_data.data)

    @pytest.mark.parametrize('expected', [
        org_expected_data,
    ])
    def test_insert_organization(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Organization.objects.count() == 0
        organization = parser.organization
        assert Organization.objects.count() == 1
        for key, value in expected.items():
            assert getattr(organization, key) == value

    @pytest.mark.parametrize('expected', [
        org_expected_data,
    ])
    def test_update_organization(self, cluster, cluster_sync_data, organizations, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Organization.objects.count() == 2
        organization = parser.organization
        assert Organization.objects.count() == 2
        for key, value in expected.items():
            assert getattr(organization, key) == value

    @pytest.mark.parametrize('expected', [
        job_template_expected_data
    ])
    def test_insert_job_template(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert JobTemplate.objects.count() == 0
        job_template = parser.job_template
        assert JobTemplate.objects.count() == 1
        for key, value in expected.items():
            assert getattr(job_template, key) == value

    @pytest.mark.parametrize('expected', [
        job_template_expected_data
    ])
    def test_update_job_template(self, cluster, cluster_sync_data, job_templates, expected):
        parser = DataParser(cluster_sync_data.id)
        assert JobTemplate.objects.count() == 3
        job_template = parser.job_template
        assert JobTemplate.objects.count() == 3
        for key, value in expected.items():
            assert getattr(job_template, key) == value

    def test_job_template_calculate_manual_execution_time(self, cluster, cluster_sync_data_elapsed):
        parser = DataParser(cluster_sync_data_elapsed.id)
        job_template = parser.job_template
        assert JobTemplate.objects.count() == 1
        assert job_template.time_taken_manually_execute_minutes == 299

    @pytest.mark.parametrize('expected', [
        aap_user_expected_data,
    ])
    def test_insert_launched_by(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert AAPUser.objects.count() == 0
        launched_by = parser.launched_by
        assert AAPUser.objects.count() == 1
        for key, value in expected.items():
            assert getattr(launched_by, key) == value

    @pytest.mark.parametrize('expected', [
        aap_user_expected_data
    ])
    def test_update_launched_by(self, cluster, cluster_sync_data, aap_user, expected):
        parser = DataParser(cluster_sync_data.id)
        assert AAPUser.objects.count() == 1
        launched_by = parser.launched_by
        assert AAPUser.objects.count() == 1
        for key, value in expected.items():
            assert getattr(launched_by, key) == value

    @pytest.mark.parametrize('expected', [
        inventory_expected_data
    ])
    def test_insert_inventory(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Inventory.objects.count() == 0
        inventory = parser.inventory
        assert Inventory.objects.count() == 1
        for key, value in expected.items():
            assert getattr(inventory, key) == value

    @pytest.mark.parametrize('expected', [
        inventory_expected_data
    ])
    def test_update_inventory(self, cluster, cluster_sync_data, inventory, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Inventory.objects.count() == 1
        inventory = parser.inventory
        assert Inventory.objects.count() == 1
        for key, value in expected.items():
            assert getattr(inventory, key) == value

    @pytest.mark.parametrize('expected', [
        ee_expected_data
    ])
    def test_insert_execution_environment(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert ExecutionEnvironment.objects.count() == 0
        execution_environment = parser.execution_environment
        assert ExecutionEnvironment.objects.count() == 1
        for key, value in expected.items():
            assert getattr(execution_environment, key) == value

    @pytest.mark.parametrize('expected', [
        ee_expected_data
    ])
    def test_update_execution_environment(self, cluster, cluster_sync_data, execution_environment, expected):
        parser = DataParser(cluster_sync_data.id)
        assert ExecutionEnvironment.objects.count() == 1
        execution_environment = parser.execution_environment
        assert ExecutionEnvironment.objects.count() == 1
        for key, value in expected.items():
            assert getattr(execution_environment, key) == value

    @pytest.mark.parametrize('expected', [
        instance_group_expected_data
    ])
    def test_insert_instance_group(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert InstanceGroup.objects.count() == 0
        instance_group = parser.instance_group
        assert InstanceGroup.objects.count() == 1
        for key, value in expected.items():
            assert getattr(instance_group, key) == value

    @pytest.mark.parametrize('expected', [
        instance_group_expected_data
    ])
    def test_update_instance_group(self, cluster, cluster_sync_data, instance_group, expected):
        parser = DataParser(cluster_sync_data.id)
        assert InstanceGroup.objects.count() == 1
        instance_group = parser.instance_group
        assert InstanceGroup.objects.count() == 1
        for key, value in expected.items():
            assert getattr(instance_group, key) == value

    @pytest.mark.parametrize('expected', [
        {"name": "Label A", "cluster_id": 1, "external_id": 1},
    ])
    def test_insert_label(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        label_obj = LabelModelSchema(id=1, name="Label A")
        assert Label.objects.count() == 0
        label = parser.get_label(label_obj)
        assert Label.objects.count() == 1
        for key, value in expected.items():
            assert getattr(label, key) == value

    @pytest.mark.parametrize('expected', [
        {"name": "Label A updated", "cluster_id": 1, "external_id": 1},
    ])
    def test_update_label(self, cluster, cluster_sync_data, labels, expected):
        parser = DataParser(cluster_sync_data.id)
        label_obj = LabelModelSchema(id=1, name="Label A updated")
        assert Label.objects.count() == 3
        label = parser.get_label(label_obj)
        assert Label.objects.count() == 3
        for key, value in expected.items():
            assert getattr(label, key) == value

    @pytest.mark.parametrize('expected', [
        project_expected_data
    ])
    def test_insert_project(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Project.objects.count() == 0
        project = parser.project
        assert Project.objects.count() == 1
        for key, value in expected.items():
            assert getattr(project, key) == value

    @pytest.mark.parametrize('expected', [
        project_expected_data
    ])
    def test_update_project(self, cluster, cluster_sync_data, projects, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Project.objects.count() == 2
        project = parser.project
        assert Project.objects.count() == 2
        for key, value in expected.items():
            assert getattr(project, key) == value

    @pytest.mark.parametrize('expected', [
        host_expected_data
    ])
    def test_insert_host(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Host.objects.count() == 0
        host_obj = NameDescriptionModelSchema(id=3, name="Host C", description="Host C description")
        host = parser.get_host(host_obj, host_name="Host C")
        assert Host.objects.count() == 1
        for key, value in expected.items():
            assert getattr(host, key) == value

    @pytest.mark.parametrize('expected', [
        host_expected_data
    ])
    def test_update_host(self, cluster, cluster_sync_data, hosts, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Host.objects.count() == 3
        host_obj = NameDescriptionModelSchema(id=3, name="Host C", description="Host C description")
        host = parser.get_host(host_obj, host_name="Host C")
        assert Host.objects.count() == 3
        for key, value in expected.items():
            assert getattr(host, key) == value

    @pytest.mark.parametrize('expected', [
        host_summaries_expected_data
    ])
    def test_host_summaries(self, mocker, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        hosts = [
            Host(id=1, name="Host B", description="", external_id=2, cluster=cluster),
            Host(id=2, name="Host C", description="", external_id=2, cluster=cluster),
        ]
        host_summaries_mock = mocker.patch('backend.apps.clusters.parser.DataParser.get_host')
        host_summaries_mock.side_effect = hosts
        host_summaries = list(parser.host_summaries)
        assert len(host_summaries) == 2
        for i, data in enumerate(expected):
            for key, value in data.items():
                assert host_summaries[i][key] == value
            assert host_summaries[i]["host"] == hosts[i]

    @pytest.mark.parametrize('expected', [
        job_expected_data
    ])
    def test_job(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        job = parser.job
        assert job == expected

    @pytest.mark.parametrize('expected', [
        parsed_job_expected_data
    ])
    def test_parse(self, cluster, cluster_sync_data, expected):
        parser = DataParser(cluster_sync_data.id)
        assert Job.objects.count() == 0
        assert JobHostSummary.objects.count() == 0
        parser.parse()
        db_data = Job.objects.all()
        assert len(db_data) == 1
        for key, value in expected["job"].items():
            assert getattr(db_data[0], key) == value

        db_hosts_data = JobHostSummary.objects.all()
        assert len(db_hosts_data) == 2
        for i, data in enumerate(expected["host_summaries"]):
            for key, value in data.items():
                assert getattr(db_hosts_data[i], key) == value
