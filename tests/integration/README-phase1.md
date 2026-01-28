# AAP Instance Setup (Phase 1)

**Purpose**: Automatically setup and manage AAP instances for integration testing

## Quick Start

```bash
# Start AAP 2.6 (default)
./setup_aap.sh

# Wait ~10 minutes for AAP startup
# Access AAP at http://localhost:44926
# Admin password in $AAP_PASSWORD environment variable
```

## Prerequisites

**Required Tools**:
- Docker OR Podman
- Git
- curl
- jq (for JSON processing)

**System Resources**:
- 10GB free disk space in `/tmp`
- 10GB free disk space in current directory
- Ports 44925/44926 available

**Check Prerequisites**:
```bash
# Check tools
command -v docker || command -v podman
command -v git
command -v curl
command -v jq

# Check disk space
df -h /tmp
df -h .

# Check ports
ss -tuln | grep -E '44925|44926'
```

## Usage

### setup_aap.sh

Start AAP instance for integration testing.

**Syntax**:
```bash
./setup_aap.sh [OPTIONS]
```

**Options**:
- `--aap-version VERSION` - AAP version to start (2.5 or 2.6, default: 2.6)
- `--aap-dev-version REF` - Git ref for aap-dev checkout (commit/branch/tag, default: main)
- `--skip-aap` - Skip AAP startup, reuse existing instance

**Examples**:
```bash
# Start AAP 2.6 (default)
./setup_aap.sh

# Start AAP 2.5
./setup_aap.sh --aap-version 2.5

# Use specific aap-dev version
./setup_aap.sh --aap-dev-version v2.6.1

# Reuse existing AAP instance
./setup_aap.sh --skip-aap
```

**Output**:
- `aap_access.json` - Connection configuration
- Environment variables: `AAP_URL`, `AAP_PASSWORD`, `AAP_VERSION`, `AAP_USERNAME`
- `aap-dev/` directory - Repository clone

### cleanup_aap.sh

Stop AAP instance and free resources.

**Syntax**:
```bash
./cleanup_aap.sh [OPTIONS]
```

**Options**:
- `--version VERSION` - Clean specific AAP version (optional, cleans all if not specified)
- `--remove-aap-dev` - Remove aap-dev directory
- `--force` - Skip confirmation prompts

**Examples**:
```bash
# Stop AAP with confirmation
./cleanup_aap.sh

# Stop AAP without confirmation
./cleanup_aap.sh --force

# Stop and remove aap-dev directory
./cleanup_aap.sh --remove-aap-dev --force

# Clean specific version
./cleanup_aap.sh --version 2.6 --force
```

## aap_access.json Structure

Generated configuration file with AAP connection details:

```json
{
  "client_id": null,              // Phase 2+ (OAuth2)
  "client_secret": null,          // Phase 2+ (OAuth2)
  "access_token": null,           // Phase 2+ (OAuth2)
  "refresh_token": null,          // Phase 2+ (OAuth2)
  "aap_url": "http://localhost:44926",
  "aap_protocol": "http",
  "aap_address": "localhost",
  "aap_port": "44926",
  "aap_version": "2.6",
  "aap_password": "<admin-password>"
}
```

**Fields**:
- `client_id`, `client_secret`, `access_token`, `refresh_token` - OAuth2 credentials (null in Phase 1, populated in Phase 2+)
- `aap_url` - Full AAP URL
- `aap_protocol` - Protocol (http/https)
- `aap_address` - Hostname/IP
- `aap_port` - Port number as string
- `aap_version` - AAP version (2.5/2.6)
- `aap_password` - Admin password

## Port Mapping

| AAP Version | Port | URL |
|-------------|------|-----|
| 2.5 | 44925 | http://localhost:44925 |
| 2.6 | 44926 | http://localhost:44926 |

## Troubleshooting

### Missing Prerequisites

**Problem**: "Neither docker nor podman found"

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install docker.io

# Fedora/RHEL
sudo dnf install docker
# OR
sudo dnf install podman
```

---

### Insufficient Disk Space

**Problem**: "Insufficient disk space in /tmp" or "Insufficient disk space in current directory"

**Solution**:
```bash
# Check available space
df -h /tmp
df -h .

# Clean Docker images
docker system prune -a

# Move to filesystem with more space
cd /path/with/more/space
```

---

### Port Conflicts

**Problem**: "Port 44926 already in use"

**Solution**:
```bash
# Find process using port
sudo lsof -i :44926
# OR
ss -tlnp | grep 44926

# Kill old AAP instance
./cleanup_aap.sh --force

# OR kill specific process
sudo kill <PID>
```

---

### Health Check Timeout

**Problem**: "Health check timeout after 600s"

**Possible Causes**:
1. Slow system (needs >10min)
2. Network issues downloading images
3. AAP startup failure

**Solution**:
```bash
# Check container status
docker ps -a

# Check container logs
docker logs <container-id>

# Check aap-dev logs (if available)
cd aap-dev && ls -la

# Retry with verbose mode
bash -x ./setup_aap.sh
```

---

### Admin Password Not Found

**Problem**: "Admin password not found"

**Solution**:
```bash
# Retrieve password from aap-dev
cd aap-dev
make admin-password

# Check environment variable
echo $AAP_PASSWORD

# Read from config file
cat ../aap_access.json | jq -r '.aap_password'
```

---

### Debugging

**Commands for troubleshooting**:
```bash
# Run setup with verbose output
bash -x ./setup_aap.sh

# Check container status
docker ps -a

# Follow container logs
docker logs -f <container-id>

# Test AAP connectivity
curl -k http://localhost:44926/api/gateway/v1/ping/

# Read aap-dev documentation
xdg-open https://github.com/ansible/aap-dev
```

## Common Workflows

### Daily Development
```bash
# Morning: Start AAP once
./setup_aap.sh

# During day: Reuse existing AAP
./setup_aap.sh --skip-aap

# Evening: Clean up
./cleanup_aap.sh --force
```

### Testing Multiple Versions
```bash
# Test AAP 2.6
./setup_aap.sh --aap-version 2.6
# ... run tests ...
./cleanup_aap.sh --force

# Test AAP 2.5
./setup_aap.sh --aap-version 2.5
# ... run tests ...
./cleanup_aap.sh --force
```

### Using Specific aap-dev Version
```bash
# Use tagged release
./setup_aap.sh --aap-dev-version v2.6.1

# Use specific commit
./setup_aap.sh --aap-dev-version abc123def456

# Use branch
./setup_aap.sh --aap-dev-version stable-2.6
```

## Expected Behavior

### Startup Timeline

| Time | Phase | What's Happening |
|------|-------|------------------|
| 0s | Prerequisites Check | Validates tools, disk space, ports |
| 10s | Repository Setup | Clones aap-dev (~500MB) |
| 30s | AAP Installation | Downloads AAP images (~8GB) |
| 5-10min | AAP Startup | Starts containers, initializes database |
| 10min | Health Check | Polls API until ready |
| 10min | Credentials | Retrieves admin password |
| 10min | Configuration | Generates aap_access.json |

**Total Time**: 10-15 minutes (typical), up to 20 minutes on slow systems

### Success Indicators

```
[PHASE] Prerequisites Check
[INFO] Docker found: /usr/bin/docker
[INFO] Git found: /usr/bin/git
[INFO] curl found: /usr/bin/curl
[SUCCESS] All prerequisites met

[PHASE] AAP Instance Setup
[INFO] Starting AAP 2.6 on port 44926...
[INFO] Waiting for AAP to be ready (max 600s)...
[SUCCESS] AAP instance is ready

[PHASE] Credentials Retrieval
[SUCCESS] Admin credentials validated

[PHASE] Configuration Export
[SUCCESS] Configuration exported

========================================
✅ AAP Setup Complete
========================================
AAP Version: 2.6
AAP URL: http://localhost:44926
Admin Username: admin
Admin Password: (exported in $AAP_PASSWORD)
```

## FAQ

**Q: How long does setup take?**  
A: 10-15 minutes typical, up to 20 minutes on slow systems.

**Q: Can I run multiple AAP versions simultaneously?**  
A: No, Phase 1 supports one version at a time (port conflict).

**Q: Do I need to cleanup after each test?**  
A: No, use `--skip-aap` to reuse existing instance.

**Q: Where are admin credentials stored?**  
A: In `aap_access.json` and `$AAP_PASSWORD` environment variable.

**Q: What if I already have AAP running?**  
A: Use `--skip-aap` to reuse it, or cleanup first.

**Q: How do I update aap-dev to latest version?**  
A: Run `./cleanup_aap.sh --remove-aap-dev --force` then setup again.

## Support

**For Issues**:
- Check troubleshooting section above
- Review script output for diagnostic information
- Check [aap-dev documentation](https://github.com/ansible/aap-dev)
- Run with `bash -x ./setup_aap.sh` for verbose debugging

## Next Steps

**After Phase 1 Complete**:
1. Access AAP UI at http://localhost:44926 (login: admin / $AAP_PASSWORD)
2. Verify API access: `curl -k -u admin:$AAP_PASSWORD http://localhost:44926/api/v2/me/`
3. Ready for Phase 2: `./setup_aap_data.sh` (coming soon)
