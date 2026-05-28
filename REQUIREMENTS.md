# Requirements Management

This project uses `pip` and `pip-tools` for dependency management with automated requirements file generation.

## Working with Dependencies

### Initial Development Setup

For initial development setup, follow the instructions in [README.md](README.md#backend):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements-pinned.txt
```

### Requirements Management

The Makefile provides automated requirements management:

```bash
# Sync ALL requirements files (recommended - does everything)
make requirements

# Or sync individual files:
make sync-requirements        # Generate requirements-build.txt only
make sync-build-tools         # Generate requirements-build-tools.txt only (requires podman)

# Check if requirements are in sync
make requirements-check
```

## Syncing Requirements Files

Both `requirements-build.txt` and `requirements-build-tools.txt` are automatically generated from `requirements-pinned.txt`. 

### Manual Sync

```bash
# Sync all requirements files (creates venv and installs pip-tools if needed)
make requirements
```

This will:
1. Generate `requirements-build.txt` from `requirements-pinned.txt` (with hashes)
2. Generate `requirements-build-tools.txt` from `requirements-build.txt` (build backend dependencies)

### Check if files are in sync

```bash
# Check if requirements-build.txt matches the current state
make requirements-check
```

**Note:** The `requirements-check` command will automatically run `make sync-requirements` first, then check if the generated file matches what's currently tracked in git.

## Automated Sync

The requirements files are automatically synced via:

- **Pre-commit hooks**: Automatically sync when `requirements-pinned.txt` changes
- **GitHub Actions**: 
  - On push to `main`: `requirements-build.txt` is automatically updated and committed
  - On pull requests: The workflow checks if `requirements-build.txt` is in sync and fails if it's not

If you see a PR check failure, run `make sync-requirements` locally and commit the updated `requirements-build.txt` file.

## File Contents

- `requirements-pinned.txt`: **Source of truth** - Contains exact version pins for all runtime, deployment, and development dependencies
- `requirements-build.txt`: Contains build dependencies for downstream hermetic builds, compiled from requirements-pinned.txt (auto-generated, includes hashes)
- `requirements-build-tools.txt`: Contains build-time tool dependencies (build backends) for hermetic Konflux builds, compiled from `requirements-build.txt` via `pybuild-deps` (auto-generated)

## Tricks

### Update all dependencies

Remove `requirements-build.txt`, and file will be regenerated using latest versions.

### Update a single dependency library

Example: there is vulnerability in a single dependency library.
Like [CVE-2025-6176](https://nvd.nist.gov/vuln/detail/CVE-2025-6176) - brotli<=1.1.0.
You need to upgrade brotli to >=1.2.0.
The `sync-requirement.sh` does not update all packages to latest version.
To update only `brotli`:

```bash
make sync-requirements EXTRA_DEPS="brotli>=1.2.0"

# EXTRA_DEPS can contain multiple dependencies. They need to be space-separated.
make sync-requirements EXTRA_DEPS="brotli>=1.2.0 urllib3>=0.0.1"
```
