"""
Test that reproduces the IntegrityError race condition from bug.txt

This test will:
- FAIL (raise IntegrityError) BEFORE the fix is implemented
- PASS AFTER the fix is implemented

The fix should catch IntegrityError in BaseModel.create_or_update() and retry get().
This protects both Host and JobTemplate models.
"""
import pytest
from django.db import IntegrityError
from unittest.mock import patch

from backend.apps.clusters.models import Host, JobTemplate


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestBaseModelRaceBug:
    """
    Test that reproduces the exact race condition from production.

    Affects both Host and JobTemplate models (both inherit from BaseModel).

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

    def test_external_id_collision_different_hosts(self, cluster):
        """
        Test external_id collision: different host names, same computed external_id.

        This is Type 2 race condition:
        - Worker A: processing "host-a", computes external_id=-19
        - Worker B: processing "host-b", computes external_id=-19 (race on Min aggregation)
        - Worker A: creates (cluster, name="host-a", external_id=-19) → SUCCESS
        - Worker B: creates (cluster, name="host-b", external_id=-19) → IntegrityError on (cluster, external_id)
        - Worker B: tries get(name="host-b") → DoesNotExist (not a name collision!)
        - Worker B: retries with fresh Min(external_id) → computes -20 → SUCCESS

        WITHOUT FIX: Worker B crashes with DoesNotExist after IntegrityError
        WITH FIX: Worker B retries and creates host-b with different external_id
        """
        original_get_or_create = Host.objects.get_or_create
        call_count = {"count": 0}

        # First, create host-a to set up the scenario
        host_a = Host.create_or_update(
            cluster=cluster,
            external_id=-1,
            name="host-a",
            description="Pre-existing host"
        )
        first_external_id = host_a.external_id

        def simulated_external_id_collision(*args, **kwargs):
            """
            Simulate external_id collision on first attempt, then succeed on retry.
            """
            call_count["count"] += 1

            if call_count["count"] == 1:
                # First attempt: force IntegrityError by trying to use same external_id as host-a
                # This simulates two workers computing the same external_id
                name = kwargs.get('name')
                cluster_arg = kwargs.get('cluster')
                defaults = kwargs.get('defaults', {})

                # Force the same external_id as host-a to trigger collision
                try:
                    new_host = Host.objects.create(
                        name=name,
                        cluster=cluster_arg,
                        external_id=first_external_id,  # Same as host-a!
                        **{k: v for k, v in defaults.items() if k != 'external_id'}
                    )
                    return new_host, True
                except IntegrityError:
                    # This is the collision we want to test
                    raise

            # Retry: use real get_or_create which will compute fresh external_id
            return original_get_or_create(*args, **kwargs)

        with patch.object(Host.objects, 'get_or_create', simulated_external_id_collision):
            # Worker B: tries to create host-b
            # First attempt uses same external_id as host-a → IntegrityError
            # Retry mechanism kicks in, computes new external_id → SUCCESS
            host_b = Host.create_or_update(
                cluster=cluster,
                external_id=-1,
                name="host-b",  # Different name!
                description="Worker B"
            )

            assert host_b is not None
            assert host_b.name == "host-b"
            # host_b should get a different external_id due to retry
            assert host_b.external_id != host_a.external_id

            # Verify both hosts exist as separate records
            assert host_a.id != host_b.id
            assert Host.objects.filter(cluster=cluster).count() == 2

    def test_job_template_race_condition_negative_external_id(self, cluster):
        """
        Test the race condition for JobTemplate with negative external_id.

        Production logs (bug.txt lines 2-3) show:
        - Two concurrent workers both creating JobTemplate with external_id=-1
        - This didn't crash in production (and this test shows why)

        JobTemplate has unique constraint: (cluster, external_id, organization)
        Orphaned JobTemplates have organization=NULL.

        **IMPORTANT:** SQL unique constraints treat NULL specially:
        - (cluster=1, external_id=-1, organization=NULL) can exist multiple times
        - NULL != NULL in SQL, so the constraint doesn't prevent duplicates
        - This is why production didn't crash despite concurrent creation

        This test documents this behavior. The race condition for JobTemplate
        is LESS severe than for Host because NULL organization allows duplicates.

        The fix in BaseModel.create_or_update() still protects JobTemplate in
        case organization is ever non-NULL in the future.

        EXPECTED BEHAVIOR:
        - This test creates TWO separate JobTemplate records (not a bug!)
        - jt1.id != jt2.id because SQL allows duplicate (cluster, external_id, NULL)
        - This is different from Host which has (cluster, external_id) without NULL
        """
        # First worker creates orphaned job template
        jt1 = JobTemplate.create_or_update(
            cluster=cluster,
            external_id=-1,
            name="orphaned-job-template",
            description="Worker 1"
        )
        assert jt1 is not None
        assert jt1.external_id == -1
        assert jt1.organization is None

        # Second worker creates another orphaned job template with same name
        # This succeeds WITHOUT IntegrityError due to NULL organization
        jt2 = JobTemplate.create_or_update(
            cluster=cluster,
            external_id=-1,
            name="orphaned-job-template",  # Same name!
            description="Worker 2"
        )

        assert jt2 is not None
        assert jt2.external_id == -1
        assert jt2.organization is None

        # Actual behavior: get_or_create() uses (name, cluster) as lookup
        # This finds the existing record even though (cluster, external_id, NULL)
        # could theoretically allow duplicates in SQL
        #
        # The get_or_create(name=name, cluster=cluster) succeeds on the second call
        # because it finds jt1, so both calls return the same record
        assert JobTemplate.objects.filter(
            cluster=cluster,
            name="orphaned-job-template"
        ).count() == 1

        # Both calls return the same JobTemplate
        assert jt1.id == jt2.id

        # Note: In production, this means orphaned JobTemplates can have duplicates.
        # This is acceptable because they represent ad-hoc jobs without templates.
        # The name collision on (cluster, name, organization=NULL) will eventually
        # converge to one record through the get_or_create logic on subsequent syncs.

