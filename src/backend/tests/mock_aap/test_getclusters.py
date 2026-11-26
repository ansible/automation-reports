import pytest
import yaml

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value
from backend.apps.scheduler.models import SyncSchedule
from django.core.management import call_command


@pytest.mark.django_db(transaction=True)
class TestGetClusters:
    def test_getclusters_includes_id(self, capsys):
        cluster = Cluster.objects.create(
            protocol="https",
            address="aap.example.com",
            port=443,
            access_token=encrypt_value(b"token"),
            refresh_token=encrypt_value(b"refresh"),
            client_id="dashboard",
            client_secret=encrypt_value(b"secret"),
            verify_ssl=False,
        )

        call_command("getclusters")

        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)

        assert "clusters" in output
        assert len(output["clusters"]) == 1
        cluster_dict = output["clusters"][0]

        assert cluster_dict["id"] == cluster.pk
        assert cluster_dict["address"] == "aap.example.com"
        assert cluster_dict["protocol"] == "https"
        assert cluster_dict["port"] == 443
        assert cluster_dict["client_id"] == "dashboard"
        assert cluster_dict["verify_ssl"] is False

    def test_getclusters_excludes_secrets_by_default(self, capsys):
        cluster = Cluster.objects.create(
            protocol="https",
            address="aap.example.com",
            port=443,
            access_token=encrypt_value(b"token"),
            refresh_token=encrypt_value(b"refresh"),
            client_id="dashboard",
            client_secret=encrypt_value(b"secret"),
            verify_ssl=False,
        )

        call_command("getclusters")

        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)
        cluster_dict = output["clusters"][0]

        assert "access_token" not in cluster_dict
        assert "refresh_token" not in cluster_dict
        assert "client_secret" not in cluster_dict

    def test_getclusters_includes_sync_schedules(self, capsys):
        cluster = Cluster.objects.create(
            protocol="https",
            address="aap.example.com",
            port=443,
            access_token=encrypt_value(b"token"),
            refresh_token=encrypt_value(b"refresh"),
            client_id="dashboard",
            client_secret=encrypt_value(b"secret"),
            verify_ssl=False,
        )

        SyncSchedule.objects.create(
            cluster=cluster,
            name="daily-sync",
            rrule="DTSTART;TZID=UTC:20250101T000000 FREQ=DAILY;INTERVAL=1",
            enabled=True,
        )

        call_command("getclusters")

        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)
        cluster_dict = output["clusters"][0]

        assert "sync_schedules" in cluster_dict
        assert len(cluster_dict["sync_schedules"]) == 1
        schedule = cluster_dict["sync_schedules"][0]
        assert schedule["name"] == "daily-sync"
        assert schedule["enabled"] is True
        assert "rrule" in schedule

    def test_getclusters_with_decrypt_flag(self, capsys):
        cluster = Cluster.objects.create(
            protocol="https",
            address="aap.example.com",
            port=443,
            access_token=encrypt_value(b"test-token"),
            refresh_token=encrypt_value(b"test-refresh"),
            client_id="dashboard",
            client_secret=encrypt_value(b"test-secret"),
            verify_ssl=False,
        )

        call_command("getclusters", "--decrypt")

        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)
        cluster_dict = output["clusters"][0]

        assert cluster_dict["access_token"] == "test-token"
        assert cluster_dict["refresh_token"] == "test-refresh"
        assert cluster_dict["client_secret"] == "test-secret"
