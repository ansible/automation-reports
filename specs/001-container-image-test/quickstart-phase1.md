# Quickstart: AAP Instance Setup (Phase 1)

**Last Updated**: 2026-01-26  
**Spec**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)

## TL;DR

```bash
# Start AAP 2.6 (default)
cd tests/integration
./setup_aap.sh

# Wait ~10 minutes for AAP startup
# Access AAP at http://localhost:44926
# Credentials in AAP_PASSWORD environment variable
```

---

## Prerequisites

**Before running setup:**

✅ **Required Tools**:
- Docker OR Podman
- Git
- curl

✅ **System Resources**:
- 10GB free disk space in /tmp
- 10GB free disk space in current directory
- Ports 44925/44926 available

**Check Prerequisites**:
```bash
# Check tools
command -v docker || command -v podman
command -v git
command -v curl

# Check disk space
df -h /tmp
df -h .

# Check ports
ss -tuln | grep -E '44925|44926'
```

---

## Quick Commands

### Start AAP

```bash
# AAP 2.6 (default, port 44926)
./setup_aap.sh

# AAP 2.5 (port 44925)
./setup_aap.sh --aap-version 2.5

# Use specific aap-dev version
./setup_aap.sh --aap-dev-version v2.6.1

# Reuse existing AAP (skip startup)
./setup_aap.sh --skip-aap
```

### Stop AAP

```bash
# Stop all AAP instances
./cleanup_aap.sh --force

# Stop specific version
./cleanup_aap.sh --version 2.6 --force

# Remove aap-dev directory too
./cleanup_aap.sh --remove-aap-dev --force
```

### Access AAP

```bash
# Get credentials
cat aap_access.json | jq '.aap_password'
# Or from environment
echo $AAP_PASSWORD

# Test API
curl -k -u admin:$AAP_PASSWORD \
  http://localhost:44926/api/v2/me/

# Open in browser
xdg-open http://localhost:44926
```

---

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

**Total Time**: 10-15 minutes (typical)

### Success Indicators

✅ **Setup Succeeded When**:
```
[SUCCESS] AAP instance is ready
[SUCCESS] Admin credentials validated
[SUCCESS] Configuration exported

========================================
✅ AAP Setup Complete
========================================
AAP Version: 2.6
AAP URL: http://localhost:44926
```

✅ **Files Created**:
- `aap_access.json` - Connection configuration
- `aap-dev/` - Repository clone (can be removed after)

✅ **Environment Variables**:
- `AAP_URL` - Base URL
- `AAP_PASSWORD` - Admin password
- `AAP_VERSION` - Version code (25/26)
- `AAP_USERNAME` - Always "admin"

---

## Troubleshooting

### Problem: "Neither docker nor podman found"

**Solution**:
```bash
# Install Docker
sudo apt install docker.io  # Ubuntu/Debian
sudo dnf install docker     # Fedora/RHEL

# Or install Podman
sudo dnf install podman     # Fedora/RHEL
```

---

### Problem: "Insufficient disk space"

**Solution**:
```bash
# Check space
df -h /tmp
df -h .

# Clean Docker images
docker system prune -a

# Or move to larger filesystem
cd /path/with/more/space
```

---

### Problem: "Port 44926 already in use"

**Solution**:
```bash
# Find process using port
sudo lsof -i :44926
# Or
ss -tlnp | grep 44926

# Kill old AAP instance
./cleanup_aap.sh --force

# Or kill specific process
sudo kill <PID>
```

---

### Problem: "Health check timeout after 600s"

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

# Check aap-dev logs
cd aap-dev && cat install.log

# Try again with more time
# (increase timeout in script)
```

---

### Problem: "Admin password not found"

**Solution**:
```bash
# Check aap-dev directory
ls -la ~/.aap-dev/
// no such direcotry in aap-dev. Use aap-dev docs, make sure valid scripts and command are used.

# Manually retrieve password
cat ~/.aap-dev/admin_password.txt

# Or from config
grep admin_password ~/.aap-dev/config.yml
```

---

### Problem: Need to debug further

**Debugging Commands**:
```bash
# Run with verbose output
bash -x ./setup_aap.sh

# Check AAP status
cd aap-dev && make status

# View all containers
docker ps -a

# Follow container logs
docker logs -f <container-id>

# Test AAP connectivity
curl -k http://localhost:44926/api/v2/ping/

# Read aap-dev documentation
xdg-open https://github.com/ansible/aap-dev
```

---

## Configuration Reference

### aap_access.json Structure

```json
{
  "client_id": null,              // Phase 2+
  "client_secret": null,          // Phase 2+
  "access_token": null,           // Phase 2+
  "refresh_token": null,          // Phase 2+
  "aap_url": "http://localhost:44926",
  "aap_protocol": "http",
  "aap_address": "localhost",
  "aap_port": "44926",
  "aap_version": "2.6",
  "aap_password": "<admin-pass>"
}
```

### Port Mapping

| AAP Version | Port | URL |
|-------------|------|-----|
| 2.5 | 44925 | http://localhost:44925 |
| 2.6 | 44926 | http://localhost:44926 |

### Default Credentials

| Field | Value |
|-------|-------|
| Username | admin |
| Password | From `aap_access.json` or `$AAP_PASSWORD` |

---

## Next Steps

**After Phase 1 Complete**:

1. **Access AAP UI**:
   ```bash
   xdg-open http://localhost:44926
   # Login with admin / $AAP_PASSWORD
   ```

2. **Verify API Access**:
   ```bash
   curl -k -u admin:$AAP_PASSWORD \
     http://localhost:44926/api/v2/organizations/
   ```

3. **Ready for Phase 2**:
   ```bash
   # Phase 2 will populate AAP with test data
   ./setup_aap_data.sh  # Coming soon
   ```

4. **Keep AAP Running**:
   ```bash
   # Use --skip-aap in later commands to reuse instance
   ./setup_aap.sh --skip-aap
   ```

5. **Stop When Done**:
   ```bash
   ./cleanup_aap.sh --force
   ```

---

## Common Workflows

### Daily Development

```bash
# Morning: Start AAP once
./setup_aap.sh

# During day: Reuse existing AAP
./setup_aap.sh --skip-aap
# ... do development work ...

# Evening: Clean up
./cleanup_aap.sh --force
```

### Testing Different Versions

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

---

## FAQ

**Q: How long does setup take?**  
A: 10-15 minutes typical, up to 20 minutes on slow systems.

**Q: Can I run multiple AAP versions simultaneously?**  
A: No, Phase 1 supports one version at a time (port conflict).

**Q: Do I need to cleanup after each test?**  
A: No, use `--skip-aap` to reuse existing instance.

**Q: Where are admin credentials stored?**  
A: In `aap_access.json` and `$AAP_PASSWORD` environment variable.

**Q: Can I access AAP from other machines?**  
A: By default no (localhost only). Modify aap-dev config for network access.

**Q: What if I already have AAP running?**  
A: Use `--skip-aap` to reuse it, or cleanup first.

**Q: How do I update aap-dev to latest version?**  
A: Run `./cleanup_aap.sh --remove-aap-dev --force` then setup again.

---

## Support

**For Issues**:
- Check [Troubleshooting](#troubleshooting) section above
- Review script output for diagnostic information
- Check [aap-dev documentation](https://github.com/ansible/aap-dev)
- Run with `bash -x ./setup_aap.sh` for verbose debugging
