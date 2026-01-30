# Setup Script Contract: Phase 1 AAP Instance Setup

**Version**: 1.0  
**Date**: 2026-01-26  
**Spec**: [spec-phase1-aap-setup.md](../spec-phase1-aap-setup.md)

## Script Interface

### Command: `setup_aap.sh`

**Purpose**: Automate AAP instance setup using aap-dev

**Location**: `tests/integration/setup_aap.sh`

### Command-Line Interface

```bash
./setup_aap.sh [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--aap-version` | string | No | `2.6` | AAP version to start (2.5 or 2.6) |
| `--aap-dev-version` | string | No | `main` | Git ref for aap-dev repo (commit SHA, branch, or tag) |
| `--skip-aap` | flag | No | false | Skip AAP setup, reuse existing instance |
| `--help` | flag | No | false | Show usage information |

#### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | AAP setup completed successfully |
| 1 | Prerequisites failed | Missing tool (docker, git, curl) or insufficient disk space |
| 2 | Repository error | Failed to clone/checkout aap-dev repository |
| 3 | Startup error | AAP failed to start or health check timeout |
| 4 | Validation error | Admin credentials not found or invalid |
| 5 | Configuration error | Failed to generate aap_access.json or export variables |

### Standard Output

**Format**: Structured logging with phase markers

```
[PHASE] Phase Name - Description
[INFO] Regular informational message
[ERROR] Error message with details
[SUCCESS] Success message with confirmation
```

**Example**:
```
[PHASE] Prerequisites Check - Validating required tools and disk space
[INFO] Docker found: Docker version 24.0.7
[INFO] Git found: git version 2.43.0
[INFO] Curl found: curl 8.5.0
[INFO] Disk space OK: 85GB available in /tmp
[INFO] Disk space OK: 120GB available in /home/user/project
[SUCCESS] All prerequisites satisfied

[PHASE] AAP Repository Setup - Cloning/updating aap-dev
[INFO] Cloning aap-dev from https://github.com/ansible/aap-dev
[INFO] Checking out main branch
[SUCCESS] aap-dev repository ready

[PHASE] AAP Instance Startup - Starting AAP 2.6 on port 44926
[INFO] Running: make install
[INFO] Running: make start
[INFO] Waiting for AAP to be ready (timeout: 600s)...
[INFO] Health check attempt 1/120...
[INFO] Health check attempt 2/120...
[SUCCESS] AAP instance is ready

[PHASE] Credentials Retrieval - Getting admin password
[INFO] Reading password from ~/.aap-dev/admin_password.txt
[INFO] Validating credentials with AAP API
[SUCCESS] Admin credentials validated

[PHASE] Configuration Export - Generating aap_access.json
[INFO] AAP URL: http://localhost:44926
[INFO] AAP Version: 2.6
[INFO] Writing aap_access.json
[SUCCESS] Configuration exported

========================================
✅ AAP Setup Complete
========================================
AAP Version: 2.6
AAP URL: http://localhost:44926
Admin Username: admin
Admin Password: <stored in AAP_PASSWORD>

Next steps:
  - Run ./setup_aap_data.sh to populate test data (Phase 2)
  - Or export environment variables:
      source <(grep AAP_ tests/integration/.env)
========================================
```

### Standard Error

**Purpose**: Diagnostic information on failure

**Contents**:
- Error message with context
- Container logs (last 50 lines from each AAP container)
- Disk space status
- Port status (netstat/ss output)
- Network connectivity checks
- Debugging commands to try

**Example Failure Output**:
```
[ERROR] AAP health check timeout after 600 seconds

========================================
Diagnostic Information
========================================

Container Status:
CONTAINER ID   IMAGE                      STATUS
abc123def456   quay.io/ansible/aap:2.6   Up 5 minutes (unhealthy)

Container Logs (last 50 lines):
[Container abc123def456]
ERROR: Database connection failed
ERROR: PostgreSQL service not ready
...

Disk Space:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   95G    5G  95% /

Port Status:
tcp        0      0 0.0.0.0:44926        0.0.0.0:*               LISTEN      

Network Connectivity:
✅ Internet connectivity OK
✅ localhost reachable
❌ AAP API endpoint timeout

========================================
Debugging Commands
========================================
Inspect container logs:
  docker logs abc123def456

Check AAP status:
  cd tests/integration/aap-dev && make status

View aap-dev documentation:
  https://github.com/ansible/aap-dev#readme

Retry with verbose output:
  bash -x ./setup_aap.sh --aap-version 2.6

========================================
```

---

## Output Artifacts

### 1. aap_access.json

**Location**: `tests/integration/aap_access.json`

**Format**: JSON

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "client_id", "client_secret", "access_token", "refresh_token",
    "aap_url", "aap_protocol", "aap_address", "aap_port",
    "aap_version", "aap_password"
  ],
  "properties": {
    "client_id": { "type": ["string", "null"] },
    "client_secret": { "type": ["string", "null"] },
    "access_token": { "type": ["string", "null"] },
    "refresh_token": { "type": ["string", "null"] },
    "aap_url": { "type": "string", "format": "uri" },
    "aap_protocol": { "type": "string", "enum": ["http", "https"] },
    "aap_address": { "type": "string" },
    "aap_port": { "type": "string", "pattern": "^\\d+$" },
    "aap_version": { "type": "string", "enum": ["2.5", "2.6"] },
    "aap_password": { "type": "string", "minLength": 1 }
  }
}
```

**Phase 1 Guarantees**:
- File exists at specified location
- Valid JSON syntax
- All required fields present
- OAuth2 fields (client_id, client_secret, access_token, refresh_token) are null
- aap_url is well-formed and reachable
- aap_protocol matches URL scheme
- aap_port matches AAP version (25→44925, 26→44926)
- aap_password is non-empty

### 2. Environment Variables

**Exported Variables**:

```bash
export AAP_URL="http://localhost:44926"
export AAP_PASSWORD="<admin-password>"
export AAP_VERSION="26"
export AAP_USERNAME="admin"
```

**Guarantees**:
- Variables are exported to shell environment
- AAP_URL is accessible and validated
- AAP_PASSWORD matches admin credentials
- AAP_VERSION is "25" or "26" (not "2.5" or "2.6")
- AAP_USERNAME is always "admin"

### 3. aap-dev Repository

**Location**: `tests/integration/aap-dev/`

**State**:
- Git repository cloned from https://github.com/ansible/aap-dev
- Checked out to specified version (--aap-dev-version or main)
- AAP instance running via make targets
- Admin credentials stored in ~/.aap-dev/admin_password.txt

---

## Prerequisites Contract

**The script MUST validate these before attempting setup:**

### Required Tools

| Tool | Validation | Error if Missing |
|------|------------|------------------|
| docker OR podman | `command -v docker` or `command -v podman` | Exit code 1: "Neither docker nor podman found" |
| git | `command -v git` | Exit code 1: "Git not found" |
| curl | `command -v curl` | Exit code 1: "Curl not found" |

### Disk Space

| Location | Required | Validation | Error if Insufficient |
|----------|----------|------------|----------------------|
| /tmp | 10GB | `df -BG /tmp` | Exit code 1: "Insufficient disk space in /tmp" |
| Current directory | 10GB | `df -BG .` | Exit code 1: "Insufficient disk space in current directory" |

### Ports

| Port | Version | Validation | Behavior |
|------|---------|------------|----------|
| 44925 | AAP 2.5 | `netstat -tuln \| grep 44925` or `ss -tuln \| grep 44925` | If in use: Provide command to free port |
| 44926 | AAP 2.6 | `netstat -tuln \| grep 44926` or `ss -tuln \| grep 44926` | If in use: Provide command to free port |

---

## Health Check Contract

### Endpoint

- **AAP 2.5+**: `GET /api/gateway/v1/ping/`
- **AAP 2.4**: `GET /api/v2/ping/` (fallback)

### Request

```bash
curl -s -f -k "${AAP_URL}/api/gateway/v1/ping/"
```

**Options**:
- `-s`: Silent mode (no progress bar)
- `-f`: Fail on HTTP errors (non-2xx status)
- `-k`: Allow insecure SSL (self-signed certs)

### Expected Response

**Status Code**: 200 OK

**Response Body** (AAP 2.5+):
```json
{
  "version": "2.6",
  "active_node": "aap-controller-1",
  "ha_enabled": false
}
```

### Polling Strategy

- **Interval**: 5 seconds
- **Max Attempts**: 120 (total timeout: 600 seconds)
- **Retry Logic**: Try gateway endpoint first, fall back to v2 endpoint
- **Failure**: On timeout, capture diagnostics and exit with code 3

### Success Criteria

Health check succeeds when:
1. HTTP status code is 200
2. Response body contains version field
3. Version matches expected AAP version (2.5 or 2.6)

---

## Cleanup Script Contract

### Command: `cleanup_aap.sh`

**Purpose**: Stop AAP instance and free resources

**Location**: `tests/integration/cleanup_aap.sh`

### Command-Line Interface

```bash
./cleanup_aap.sh [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--version` | string | No | all | AAP version to clean (2.5, 2.6, or all) |
| `--remove-aap-dev` | flag | No | false | Also remove aap-dev repository directory |
| `--force` | flag | No | false | Skip confirmation prompt |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - cleanup completed |
| 1 | Partial failure - some resources not cleaned |
| 2 | User cancelled (no --force and user declined) |

### Output

```
[INFO] Stopping AAP 2.6 instance...
[INFO] Running: cd aap-dev && make stop
[INFO] Removing containers...
[SUCCESS] AAP instance stopped

[INFO] Verifying port 44926 is freed...
[SUCCESS] Port 44926 is available

[INFO] Cleaning up aap_access.json...
[SUCCESS] Configuration files removed

========================================
✅ Cleanup Complete
========================================
Resources freed:
  - AAP 2.6 containers stopped
  - Port 44926 available
  - Configuration files removed

To remove aap-dev repository:
  rm -rf tests/integration/aap-dev
========================================
```

---

## Error Handling Guarantees

1. **Fast Failure**: Script exits immediately on critical errors (missing prerequisites, disk space)
2. **Clear Messages**: All errors include context and suggested fixes
3. **Diagnostic Capture**: On AAP startup failure, comprehensive diagnostics are collected
4. **Debugging Guidance**: Error output includes commands to continue investigation
5. **State Cleanup**: On failure, partial AAP setup is cleaned up (stopped containers)
6. **Idempotent**: Script can be re-run safely after fixing issues

---

## Testing Contract

**Manual Verification Required** (Phase 1):

```bash
# Test 1: AAP 2.6 setup
./setup_aap.sh --aap-version 2.6
# Verify: AAP accessible at http://localhost:44926
# Verify: aap_access.json exists with correct data
# Verify: Environment variables exported

# Test 2: AAP 2.5 setup
./cleanup_aap.sh --force
./setup_aap.sh --aap-version 2.5
# Verify: AAP accessible at http://localhost:44925

# Test 3: Skip mode
./setup_aap.sh --skip-aap
# Verify: Reuses existing AAP, no restart

# Test 4: Cleanup
./cleanup_aap.sh --force
# Verify: AAP stopped, ports freed

# Test 5: Error handling
./setup_aap.sh --aap-version 2.6
# (Simulate error: fill disk, kill network)
# Verify: Clear error message with diagnostics
```

**Success Criteria**:
- All 5 tests pass
- Script output is clear and actionable
- No manual intervention required for happy path
- Errors provide sufficient information to resolve issues
