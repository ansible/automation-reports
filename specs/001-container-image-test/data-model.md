# Data Model: Container Image Integration Test

**Feature**: Container Image Integration Test  
**Branch**: 001-container-image-test  
**Date**: 2026-01-22

## Overview

This document defines the data entities validated by the integration test. These entities represent synchronized AAP data stored in PostgreSQL after successful data synchronization.

## Core Entities

### Currency
**Purpose**: Represents monetary currencies for cost calculation  
**Source**: Created by backend during initialization (not synced from AAP)  
**Expected Count**: 5

**Fields**:
- `code` (string, PK): ISO currency code (e.g., "USD", "EUR", "GBP", "JPY", "CHF")
- `name` (string): Full currency name
- `symbol` (string): Currency symbol

**Validation Rule**: Exactly 5 currencies must exist (standard set for cost analysis)

**Relationships**: None (reference data)

---

### SyncJob
**Purpose**: Tracks data synchronization operations and parsing tasks  
**Source**: Created by backend scheduler during sync/parse operations  
**Expected Count**: 6

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `cluster_id` (integer, FK): Reference to Cluster
- `type` (enum): "sync_jobs" or "parse_job_data"
- `status` (enum): "pending", "running", "completed", "failed"
- `started_at` (timestamp): Task start time
- `completed_at` (timestamp, nullable): Task completion time
- `error_message` (text, nullable): Error details if failed

**Validation Rule**: Exactly 6 SyncJob records (2 sync_jobs + 4 parse_job_data tasks)

**Relationships**:
- Belongs to one Cluster (many-to-one)

**State Transitions**:
```
pending → running → completed
                 ↓
               failed
```

**Breakdown**:
- 2x sync_jobs type: Initial data fetch operations
- 4x parse_job_data type: Job data parsing tasks (one per job synced)

---

### AAPUser
**Purpose**: Represents AAP user accounts synced to dashboard  
**Source**: Synced from AAP `/api/v2/users/` endpoint  
**Expected Count**: 1

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_user_id` (integer, indexed): AAP user ID
- `username` (string): AAP username
- `first_name` (string, nullable): User's first name
- `last_name` (string, nullable): User's last name
- `email` (string, nullable): User's email address
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 1 AAPUser (admin user from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- May own multiple Jobs (one-to-many)

---

### Organization
**Purpose**: Represents AAP organizations  
**Source**: Synced from AAP `/api/v2/organizations/` endpoint  
**Expected Count**: 2

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_org_id` (integer, indexed): AAP organization ID
- `name` (string): Organization name
- `description` (text, nullable): Organization description
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 2 Organizations (test data from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- Has many Projects (one-to-many)
- Has many JobTemplates (one-to-many)
- Has many Inventories (one-to-many)

---

### JobTemplate
**Purpose**: Represents AAP job templates  
**Source**: Synced from AAP `/api/v2/job_templates/` endpoint  
**Expected Count**: 3

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_template_id` (integer, indexed): AAP job template ID
- `name` (string): Template name
- `description` (text, nullable): Template description
- `job_type` (enum): "run" or "check"
- `organization_id` (integer, FK): Reference to Organization
- `project_id` (integer, FK, nullable): Reference to Project
- `inventory_id` (integer, FK, nullable): Reference to Inventory
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 3 JobTemplates (test data from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- Belongs to one Organization (many-to-one)
- May belong to one Project (many-to-one)
- May belong to one Inventory (many-to-one)
- Has many Jobs (one-to-many)

---

### Job
**Purpose**: Represents AAP job executions  
**Source**: Synced from AAP `/api/v2/jobs/` endpoint  
**Expected Count**: 4

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_job_id` (integer, indexed): AAP job ID
- `name` (string): Job name
- `status` (enum): "pending", "running", "successful", "failed", "canceled"
- `started` (timestamp, nullable): Job start time
- `finished` (timestamp, nullable): Job completion time
- `elapsed` (float, nullable): Job duration in seconds
- `job_template_id` (integer, FK, nullable): Reference to JobTemplate
- `organization_id` (integer, FK): Reference to Organization
- `created_by_id` (integer, FK, nullable): Reference to AAPUser
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 4 Jobs (test data from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- Belongs to one Organization (many-to-one)
- May belong to one JobTemplate (many-to-one)
- May be created by one AAPUser (many-to-one)
- Has many Labels (many-to-many via JobLabel)
- Has many JobHostSummaries (one-to-many)

---

### Project
**Purpose**: Represents AAP projects (SCM repositories)  
**Source**: Synced from AAP `/api/v2/projects/` endpoint  
**Expected Count**: 2

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_project_id` (integer, indexed): AAP project ID
- `name` (string): Project name
- `description` (text, nullable): Project description
- `scm_type` (enum): "git", "svn", "hg", "insights", ""
- `scm_url` (string, nullable): Source control URL
- `organization_id` (integer, FK): Reference to Organization
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 2 Projects (test data from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- Belongs to one Organization (many-to-one)
- Has many JobTemplates (one-to-many)

---

### Label
**Purpose**: Represents AAP labels for job organization  
**Source**: Synced from AAP `/api/v2/labels/` endpoint  
**Expected Count**: 2

**Fields**:
- `id` (integer, PK): Auto-incrementing identifier
- `aap_label_id` (integer, indexed): AAP label ID
- `name` (string): Label name
- `organization_id` (integer, FK): Reference to Organization
- `cluster_id` (integer, FK): Reference to Cluster

**Validation Rule**: Exactly 2 Labels (test data from setup_aap.py)

**Relationships**:
- Belongs to one Cluster (many-to-one)
- Belongs to one Organization (many-to-one)
- Applied to many Jobs (many-to-many via JobLabel)

**Note**: JobLabel is a join table (not validated separately) with 6 total label assignments across 4 jobs.

---

## Entity Relationship Diagram

```
Cluster (1)
  ├─── Currency (5) [reference data, not FK-linked]
  ├─── SyncJob (6)
  ├─── AAPUser (1)
  ├─── Organization (2)
  │     ├─── Project (2)
  │     ├─── JobTemplate (3)
  │     │     └─── Job (4)
  │     │           ├─── JobLabel (6 assignments)
  │     │           └─── JobHostSummary (4)
  │     └─── Label (2)
  └─── ... (other entities not validated in this test)
```

## Validation Contract

The validation script (`validate_results.py`) MUST assert these exact counts:

```python
assert Currency.objects.count() == 5, "Expected 5 Currency objects"
assert SyncJob.objects.count() == 6, "Expected 6 SyncJob objects"
assert AAPUser.objects.count() == 1, "Expected 1 AAPUser object"
assert Organization.objects.count() == 2, "Expected 2 Organization objects"
assert JobTemplate.objects.count() == 3, "Expected 3 JobTemplate objects"
assert Job.objects.count() == 4, "Expected 4 Job objects"
assert Project.objects.count() == 2, "Expected 2 Project objects"
assert Label.objects.count() == 2, "Expected 2 Label objects"
```

## Data Dependencies

1. **Cluster**: Must be created first via `setclusters` command
2. **Currency**: Created during Django initialization (migrations)
3. **Organizations → Projects, JobTemplates**: Hierarchical sync order
4. **JobTemplates → Jobs**: Jobs reference templates
5. **Jobs → Labels**: Many-to-many relationship created during sync
6. **SyncJob**: Created by scheduler throughout sync process

## Test Data Source

All expected counts are based on deterministic test data created by:
- **Script**: `src/backend/tests/mock_aap/setup_aap.py`
- **Reference Test**: `src/backend/tests/mock_aap/test_full.py`
- **AAP Version**: 2.5 or 2.6 (both produce same object counts)

## Excluded Entities

The following entities exist in the database schema but are NOT validated by this integration test (out of scope):
- ClusterSyncData (internal state)
- ClusterSyncStatus (internal state)
- Inventory, Host, ExecutionEnvironment, InstanceGroup (not focus of test)
- JobHostSummary (validated count-wise in test_full.py but not primary focus)
- Costs (computed later, not immediate sync result)
- FilterSet, Settings (configuration, not sync data)
