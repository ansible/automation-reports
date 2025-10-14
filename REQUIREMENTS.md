# Requirements Management

This project uses `pip` and `pip-tools` for dependency management with automated requirements file generation.

## Working with Dependencies

### Adding/Updating Dependencies

To add or update dependencies, edit the `requirements.txt` file directly:

```bash
# Edit requirements.txt to add/update dependencies
vim requirements.txt

# Sync the pinned requirements files
./sync-requirements.sh
# or
make sync-requirements
```

### Installing Dependencies

```bash
# Install production dependencies
pip install -r requirements-pinned.txt

# Install build dependencies
pip install -r requirements-build.txt

# Install from source (for development)
pip install -r requirements.txt
```

## Syncing Requirements Files

The `requirements-pinned.txt` and `requirements-build.txt` files are automatically generated from `requirements.txt`. To update them:

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

- **Pre-commit hooks**: Automatically sync when `requirements.txt` changes
- **GitHub Actions**: 
  - On push to `main`: Files are automatically updated and committed
  - On pull requests: The workflow checks if files are in sync and fails if they're not

If you see a PR check failure, run `./sync-requirements.sh` locally and commit the updated files.

## File Contents

- `requirements.txt`: Contains the dependencies
- `requirements-pinned.txt`: Contains exact version pins and security hashes for all dependencies
- `requirements-build.txt`: Contains build dependencies compiled from requirements-pinned.txt

All generated files include:
- Exact version pins
- Security hashes for verification
- Comments showing dependency relationships
- Auto-generated headers indicating their source
