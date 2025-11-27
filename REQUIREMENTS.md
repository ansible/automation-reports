# Requirements Management

This project uses `pip` and `pip-tools` for dependency management with automated requirements file generation.

## Working with Dependencies

### Initial Development Setup

For initial development setup, follow the instructions in [README.md](README.md#backend):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt -r requirements_dev.txt
```

### Requirements Management

The Makefile provides automated requirements management:

```bash
# Sync requirements files (creates venv and installs pip-tools if needed)
make sync-requirements

# Check if requirements are in sync
make requirements-check
```

## Syncing Requirements Files

The `requirements-build.txt` file is automatically generated from `requirements-pinned.txt`. 

### Manual Sync

```bash
# Sync requirements (creates venv and installs pip-tools if needed)
make sync-requirements
```

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

- `requirements.txt`: Contains the base dependencies (for reference)
- `requirements-pinned.txt`: Contains exact version pins
- `requirements-build.txt`: Contains build dependencies for downstream hermetic builds, compiled from requirements-pinned.txt (auto-generated)
