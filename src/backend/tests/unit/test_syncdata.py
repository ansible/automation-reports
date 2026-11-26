"""Tests for syncdata management command.

Covers:
  1. Default behavior without --since/--until (interactive confirmation)
  2. Basic usage with --since and --until
  3. --cluster flag to target specific clusters
  4. Error handling for missing clusters and database issues
"""
import pytest
from django.core.management import call_command

from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster
from backend.apps.scheduler.models import SyncJob


def _make_cluster(address, port=443):
    return Cluster.objects.create(
        protocol="https",
        address=address,
        port=port,
        access_token=encrypt_value(b"tok"),
        verify_ssl=False,
    )


@pytest.mark.django_db(transaction=True)
class TestSyncdataBasicUsage:
    """Test basic syncdata command usage without advanced flags."""

    def test_syncdata_with_since_and_until(self, mocker):
        """Plain usage: syncdata --since ... --until ..."""
        c24 = _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        call_command(
            "syncdata",
            "--since=2025-01-01",
            "--until=2025-12-31",
        )

        assert SyncJob.objects.count() == 1
        job = SyncJob.objects.first()
        assert job.cluster_id == c24.pk
        assert "2025-01-01" in job.name
        assert "2025-12-31" in job.name

    def test_syncdata_without_since_until_requires_confirmation(self, mocker):
        """Plain usage: syncdata (no dates, requires Y/N prompt)"""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)
        mocker.patch("builtins.input", return_value="y")

        call_command("syncdata")

        assert SyncJob.objects.count() == 1
        job = SyncJob.objects.first()
        assert job.name == "Sync historical data"

    def test_syncdata_user_aborts_without_confirmation(self, mocker, capsys):
        """User declines confirmation prompt."""
        _make_cluster("aap24.example.com")

        mocker.patch("builtins.input", return_value="n")

        with pytest.raises(SystemExit):
            call_command("syncdata")

        captured = capsys.readouterr()
        assert "Sync aborted by user" in captured.out
        assert SyncJob.objects.count() == 0

    def test_syncdata_non_interactive_mode_requires_since_until(self, mocker, capsys):
        """Non-interactive mode (EOFError) requires explicit --since and --until."""
        _make_cluster("aap24.example.com")

        mocker.patch("builtins.input", side_effect=EOFError)

        with pytest.raises(SystemExit):
            call_command("syncdata")

        captured = capsys.readouterr()
        assert "Non-iteractive mode" in captured.out
        assert "both \"since\" and \"until\" options are mandatory" in captured.out

    def test_syncdata_with_since_only_requires_confirmation(self, mocker):
        """Specifying only --since (not --until) still requires confirmation."""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)
        mocker.patch("builtins.input", return_value="y")

        call_command("syncdata", "--since=2025-01-01")

        assert SyncJob.objects.count() == 1

    def test_syncdata_with_until_only_requires_confirmation(self, mocker):
        """Specifying only --until (not --since) still requires confirmation."""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)
        mocker.patch("builtins.input", return_value="y")

        call_command("syncdata", "--until=2025-12-31")

        assert SyncJob.objects.count() == 1

    def test_syncdata_since_greater_than_until_exits(self, mocker, capsys):
        """Exit with error if --since is after --until."""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        with pytest.raises(SystemExit):
            call_command(
                "syncdata",
                "--since=2025-12-31",
                "--until=2025-01-01",
            )

        captured = capsys.readouterr()
        assert "Start date is greater than end date" in captured.out
        assert SyncJob.objects.count() == 0


@pytest.mark.django_db(transaction=True)
class TestSyncdataClusterSelection:
    """Test --cluster flag for targeting specific clusters."""

    def test_syncdata_cluster_by_address(self, mocker):
        """--cluster=<address> selects cluster by address."""
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
        assert job.cluster_id == c26.pk

    def test_syncdata_cluster_by_pk(self, mocker):
        """--cluster=<pk> selects cluster by numeric ID."""
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

    def test_syncdata_cluster_not_found_by_address(self, mocker, capsys):
        """--cluster=<nonexistent_address> exits with error."""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        with pytest.raises(SystemExit):
            call_command(
                "syncdata",
                "--since=2025-01-01",
                "--until=2025-12-31",
                "--cluster=nonexistent.example.com",
            )

        captured = capsys.readouterr()
        assert "Cluster not found: nonexistent.example.com" in captured.out

    def test_syncdata_cluster_not_found_by_pk(self, mocker, capsys):
        """--cluster=<nonexistent_pk> exits with error."""
        _make_cluster("aap24.example.com")

        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        with pytest.raises(SystemExit):
            call_command(
                "syncdata",
                "--since=2025-01-01",
                "--until=2025-12-31",
                "--cluster=9999",
            )

        captured = capsys.readouterr()
        assert "Cluster not found with id: 9999" in captured.out

    def test_syncdata_no_clusters_exist_exits(self, mocker, capsys):
        """syncdata without --cluster exits if no clusters exist."""
        mocker.patch.object(SyncJob, "signal_start", return_value=None)

        with pytest.raises(SystemExit):
            call_command(
                "syncdata",
                "--since=2025-01-01",
                "--until=2025-12-31",
            )

        captured = capsys.readouterr()
        assert "Cluster instance does not exist" in captured.out
