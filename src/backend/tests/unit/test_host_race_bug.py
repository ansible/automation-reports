"""
Test that reproduces the IntegrityError race condition from bug.txt

This test will:
- FAIL (raise IntegrityError) BEFORE the fix is implemented
- PASS AFTER the fix is implemented

The fix should catch IntegrityError in Host.create_or_update() and retry get().
"""
import pytest
from django.db import IntegrityError
from unittest.mock import patch

from backend.apps.clusters.models import Host


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestHostRaceBug:
    """
    Test that reproduces the exact race condition from production.

    Production scenario (bug.txt line 29-30):
    - Two workers process host summaries for the same cluster
    - Both call Host.create_or_update(cluster_id=1, external_id=-19, name=...)
    - Both hit the get_or_create() path
    - Worker A: get() -> DoesNotExist -> create() -> SUCCESS
    - Worker B: get() -> DoesNotExist -> create() -> IntegrityError

    Error: duplicate key value violates unique constraint
           "clusters_host_cluster_id_external_id_b1af754d_uniq"
    DETAIL: Key (cluster_id, external_id)=(1, -19) already exists.
    """

    def test_race_condition_negative_external_id(self, cluster):
        """
        Reproduce the race condition for hosts with negative external_id.

        Negative external_id uses the get_or_create() code path (line 410-414
        in models.py) which is vulnerable to race conditions.

        WITHOUT FIX: This test raises IntegrityError
        WITH FIX: This test passes (catch IntegrityError, retry get())
        """
        # Mock get_or_create to simulate the race condition window
        original_get_or_create = Host.objects.get_or_create
        call_count = {"count": 0}

        def simulated_race_get_or_create(*args, **kwargs):
            """
            Simulate the race condition:
            - First call: DoesNotExist -> creates the record
            - Second call: DoesNotExist (concurrent, hasn't seen first create yet)
                         -> tries to create again -> IntegrityError
            """
            call_count["count"] += 1

            # First call proceeds normally
            if call_count["count"] == 1:
                return original_get_or_create(*args, **kwargs)

            # Second call simulates the race:
            # It checks if record exists, finds nothing (race window),
            # then tries to create but fails with IntegrityError
            elif call_count["count"] == 2:
                # Check if first call already created it
                name = kwargs.get('name')
                cluster_arg = kwargs.get('cluster')
                existing = Host.objects.filter(
                    name=name,
                    cluster=cluster_arg
                ).first()

                if existing:
                    # Record exists, but in the race condition window,
                    # this worker hasn't seen it yet, so it tries to create
                    # This will raise IntegrityError due to unique constraint
                    defaults = kwargs.get('defaults', {})
                    external_id = defaults.get('external_id')

                    # Directly create to trigger IntegrityError
                    # (simulating what happens when get() returns DoesNotExist
                    # but another worker already created it)
                    try:
                        new_host = Host.objects.create(
                            name=name,
                            cluster=cluster_arg,
                            external_id=external_id,
                            **{k: v for k, v in defaults.items() if k != 'external_id'}
                        )
                        return new_host, True
                    except IntegrityError:
                        # This is the bug! IntegrityError is raised
                        raise

                return original_get_or_create(*args, **kwargs)

            return original_get_or_create(*args, **kwargs)

        with patch.object(Host.objects, 'get_or_create', simulated_race_get_or_create):
            # First worker creates the host
            host1 = Host.create_or_update(
                cluster=cluster,
                external_id=-1,  # Negative ID triggers get_or_create path
                name="concurrent-host",
                description="Worker 1"
            )
            assert host1 is not None
            assert host1.external_id == -1

            # Second worker tries to create the same host
            # WITHOUT FIX: This raises IntegrityError
            # WITH FIX: This catches IntegrityError and retries get(), returning existing host
            host2 = Host.create_or_update(
                cluster=cluster,
                external_id=-1,
                name="concurrent-host",  # Same name
                description="Worker 2"
            )

            # After fix, both should return the same host
            assert host2 is not None
            assert host1.id == host2.id
            assert Host.objects.filter(cluster=cluster, name="concurrent-host").count() == 1

    def test_race_condition_update_or_create_path(self, cluster):
        """
        Test the update_or_create code path (positive external_id).

        This path (line 400-404) uses update_or_create which is slightly
        better but can still have issues if name changes between calls.

        WITHOUT FIX: May raise IntegrityError in edge cases
        WITH FIX: Should handle gracefully
        """
        original_update_or_create = Host.objects.update_or_create
        call_count = {"count": 0}

        def simulated_race_update_or_create(*args, **kwargs):
            """Simulate race on update_or_create path"""
            call_count["count"] += 1

            if call_count["count"] == 1:
                return original_update_or_create(*args, **kwargs)
            elif call_count["count"] == 2:
                # Force a race by trying to get first, if not found, create
                # This can fail if between get and create another worker creates it
                name = kwargs.get('name')
                cluster_arg = kwargs.get('cluster')

                try:
                    existing = Host.objects.get(name=name, cluster=cluster_arg)
                    # Update it
                    defaults = kwargs.get('defaults', {})
                    for key, value in defaults.items():
                        setattr(existing, key, value)
                    existing.save()
                    return existing, False
                except Host.DoesNotExist:
                    # Try to create, but it might already exist now
                    return original_update_or_create(*args, **kwargs)

            return original_update_or_create(*args, **kwargs)

        with patch.object(Host.objects, 'update_or_create', simulated_race_update_or_create):
            # First worker
            host1 = Host.create_or_update(
                cluster=cluster,
                external_id=42,  # Positive ID
                name="positive-id-host",
                description="Worker 1"
            )

            # Second worker - same external_id
            # Should update, not create
            host2 = Host.create_or_update(
                cluster=cluster,
                external_id=42,
                name="positive-id-host",
                description="Worker 2"
            )

            assert host1.id == host2.id

