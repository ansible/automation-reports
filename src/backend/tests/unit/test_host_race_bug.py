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

    def test_direct_integrity_error_simulation(self, cluster):
        """
        Directly simulate what happens in production:
        Two concurrent calls to get_or_create for the same (name, cluster)
        where both think the record doesn't exist.

        WITHOUT FIX: Second call raises IntegrityError
        WITH FIX: Second call catches IntegrityError and retries get()
        """
        # Directly use the get_or_create pattern from models.py line 410
        name = "direct-test-host"
        external_id = -99

        # First call - creates the record
        host1, created1 = Host.objects.get_or_create(
            name=name,
            cluster=cluster,
            defaults={'external_id': external_id, 'description': 'First'}
        )
        assert created1 is True

        # Now mock get() to simulate the race condition
        original_get = Host.objects.get

        def race_condition_get(*args, **kwargs):
            # Make it think the record doesn't exist
            # (simulating the window where Worker B hasn't seen Worker A's create)
            raise Host.DoesNotExist()

        # Second call with mocked get() to force DoesNotExist
        # This simulates Worker B checking right before Worker A creates
        with patch.object(Host.objects, 'get', race_condition_get):
            # This will:
            # 1. Call get() -> DoesNotExist (mocked)
            # 2. Try to create() -> IntegrityError (host1 already exists)
            # WITHOUT FIX: Raises IntegrityError
            # WITH FIX: Catches IntegrityError, calls get() again without mock, succeeds
            with pytest.raises(IntegrityError) as exc_info:
                host2, created2 = Host.objects.get_or_create(
                    name=name,
                    cluster=cluster,
                    defaults={'external_id': external_id, 'description': 'Second'}
                )

            # Verify it's the expected IntegrityError
            assert "clusters_host_cluster_id_external_id" in str(exc_info.value)
            assert "already exists" in str(exc_info.value)

        # After implementing the fix, this test should be updated to:
        # 1. Remove pytest.raises
        # 2. Assert that host2.id == host1.id
        # 3. Assert created2 is False
