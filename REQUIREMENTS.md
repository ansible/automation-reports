# Requirements Management

This project uses `pip` and `pip-tools` for dependency management with automated requirements file generation.

## Working with Dependencies

### Installing Dependencies

```bash
# Install from source (for development)
pip install -r requirements.txt

# Install build dependencies
pip install -r requirements-build.txt
```

## Syncing Requirements Files

The `requirements-build.txt` file is automatically generated from `requirements-pinned.txt`. To update it:

### Manual Sync

```bash
# Using the script directly
./sync-requirements.sh

# Using make
make sync-requirements
```

### Check if files are in sync

```bash
make requirements-check
```

## Automated Sync

The requirements files are automatically synced via:

- **Pre-commit hooks**: Automatically sync when `requirements-pinned.txt` changes
- **GitHub Actions**: 
  - On push to `main`: `requirements-build.txt` is automatically updated and committed
  - On pull requests: The workflow checks if `requirements-build.txt` is in sync and fails if it's not

If you see a PR check failure, run `./sync-requirements.sh` locally and commit the updated `requirements-build.txt` file.

## File Contents

- `requirements.txt`: Contains the base dependencies (for reference)
- `requirements-pinned.txt`: Contains exact version pins
- `requirements-build.txt`: Contains build dependencies for downstream hermetic builds, compiled from requirements-pinned.txt (auto-generated)
