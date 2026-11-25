"""Tests for AAP-90152: two-cluster cutover gap fixes.

Covers:
  1. setclusters --prune-unknown-clusters deletes omitted clusters
  2. syncdata --cluster selects the correct cluster by address or pk
"""
import json

import pytest
import yaml
from django.core.management import call_command

from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster, Job, JobTypeChoices, JobLaunchTypeChoices
from backend.apps.scheduler.models import SyncJob


RRULE = "DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=MINUTELY;INTERVAL=1"


def _make_cluster(address, port=443):
    return Cluster.objects.create(
        protocol="https",
        address=address,
        port=port,
        access_token=encrypt_value(b"tok"),
        verify_ssl=False,
    )


def _clusters_yaml(tmp_path, clusters_list):
    """Write a clusters.yaml and return its path."""
    path = tmp_path / "clusters.yaml"
    path.write_text(yaml.dump({"clusters": clusters_list}))
    return str(path)


def _cluster_entry(address, port=443):
    return {
        "protocol": "https",
        "address": address,
        "port": port,
        "access_token": "tok",
        "refresh_token": "tok",
        "client_id": "dashboard",
        "client_secret": "sec",
        "verify_ssl": False,
        "sync_schedules": [{"name": "every-1m", "rrule": RRULE, "enabled": True}],
    }


# ── setclusters --prune-unknown-clusters ───────────────────────────


@pytest.mark.django_db(transaction=True)
class TestSetClustersPruneUnknown:
    """Default behavior retains clusters absent from YAML; --prune-unknown-clusters deletes them."""

    def test_default_retains_omitted_cluster(self, tmp_path, capsys, mocker):
        from backend.apps.scheduler.models import SyncSchedule

        mocker.patch(
            "backend.apps.clusters.connector.ApiConnector.check_aap_version",
            return_value=None,
        )

        c24 = _make_cluster("aap24.example.com")
        c26 = _make_cluster("aap26.example.com")

        Job.objects.create(
            type=JobTypeChoices.JOB,
            launch_type=JobLaunchTypeChoices.MANUAL,
            name="demo-job",
            cluster=c24,
            external_id=1,
        )

        SyncSchedule.objects.create(
            cluster=c24,
            name="sync-schedule",
            rrule=RRULE,
            enabled=True,
        )

        yaml_path = _clusters_yaml(tmp_path, [_cluster_entry("aap26.example.com")])

        call_command("setclusters", "--keep", yaml_path)

        assert Cluster.objects.filter(address="aap24.example.com").exists(), \
            "Omitted cluster should survive by default"
        assert Job.objects.filter(cluster=c24).count() == 1, \
            "Jobs on the omitted cluster should survive"

        sync_schedule = SyncSchedule.objects.get(cluster=c24)
        assert sync_schedule.enabled is False, \
            "Sync schedules for omitted cluster should be disabled"

        captured = capsys.readouterr()
        assert "retained" in captured.out.lower()
        assert "disabling sync schedules" in captured.out.lower()

    def test_prune_flag_deletes_unknown_clusters(self, tmp_path, capsys, mocker):
        mocker.patch(
            "backend.apps.clusters.connector.ApiConnector.check_aap_version",
            return_value=None,
        )

        _make_cluster("aap24.example.com")
        _make_cluster("aap26.example.com")

        yaml_path = _clusters_yaml(tmp_path, [_cluster_entry("aap26.example.com")])

        call_command("setclusters", "--keep", "--prune-unknown-clusters", yaml_path)

        assert not Cluster.objects.filter(address="aap24.example.com").exists(), \
            "With --prune-unknown-clusters the omitted cluster must be deleted"


# ── syncdata --cluster ──────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
class TestSyncdataClusterFlag:
    """syncdata --cluster selects the correct cluster."""

    def test_cluster_by_address(self, mocker):
        c24 = _make_cluster("aap24.example.com")
        c26 = _make_cluster("aap26.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        call_command(
            "syncdata",
            "--since=2025-01-01",
            "--until=2025-12-31",
            "--cluster=aap26.example.com",
        )

        assert SyncJob.objects.count() == 1
        job = SyncJob.objects.first()
        assert job.cluster_id == c26.pk, \
            "SyncJob must target the cluster specified by --cluster address"

    def test_cluster_by_pk(self, mocker):
        c24 = _make_cluster("aap24.example.com")
        c26 = _make_cluster("aap26.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        call_command(
            "syncdata",
            "--since=2025-01-01",
            "--until=2025-12-31",
            f"--cluster={c26.pk}",
        )

        assert SyncJob.objects.count() == 1
        job = SyncJob.objects.first()
        assert job.cluster_id == c26.pk

    def test_without_cluster_flag_falls_back_to_first(self, mocker):
        c24 = _make_cluster("aap24.example.com")
        c26 = _make_cluster("aap26.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        call_command(
            "syncdata",
            "--since=2025-01-01",
            "--until=2025-12-31",
        )

        first = Cluster.objects.first()
        job = SyncJob.objects.first()
        assert job.cluster_id == first.pk, \
            "Without --cluster, legacy behaviour (first()) must be preserved"

    def test_cluster_not_found_exits(self, mocker):
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        with pytest.raises(SystemExit):
            call_command(
                "syncdata",
                "--since=2025-01-01",
                "--until=2025-12-31",
                "--cluster=nonexistent.example.com",
            )
