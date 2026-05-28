# If you are running an old version, you might need docker-compose instead
DOCKER_COMPOSE?=docker compose

docker-compose:
	$(DOCKER_COMPOSE) --file compose/compose.yml up

# Requirements management
sync-requirements:
	@echo "Syncing requirements-build.txt from requirements-pinned.txt..."
	@if ! command -v python3.12 >/dev/null 2>&1; then \
		echo "Error: Python 3.12 is not installed or not in PATH"; \
		echo "Please install Python 3.12 or ensure it's available in your PATH"; \
		echo "You can check available Python versions with: python3 --version"; \
		exit 1; \
	fi
	@if [ ! -f .venv/bin/activate ]; then \
		echo "Virtual environment not found. Creating one with Python 3.12..."; \
		python3.12 -m venv .venv; \
		echo "Virtual environment created successfully."; \
	fi
	@source .venv/bin/activate && \
		if [ ! -f .venv/bin/pip-compile ]; then \
			echo "Installing pip-tools..."; \
			pip install pip-tools; \
		fi && \
		./sync-requirements.sh $${EXTRA_DEPS:-}
# above - we want to split EXTRA_DEPS on spaces, so we use normal shell splitting

requirements:
	@echo "Syncing all requirements files from requirements-pinned.txt..."
	@echo "Step 1/2: Generating requirements-build.txt..."
	@make sync-requirements
	@echo "Step 2/2: Generating requirements-build-tools.txt..."
	@make sync-build-tools
	@echo "All requirements files synced successfully!"

requirements-check:
	@echo "Checking if all requirements files are in sync..."
	@make requirements
	@if ! git diff --quiet requirements-build.txt requirements-build-tools.txt; then \
		echo "Requirements files are out of sync. Run 'make requirements' to update them."; \
		git diff requirements-build.txt requirements-build-tools.txt; \
		exit 1; \
	else \
		echo "All requirements files are in sync."; \
	fi

sync-build-tools:
	@echo "Regenerating requirements-build-tools.txt via pybuild-deps container..."
	@if ! command -v podman >/dev/null 2>&1; then \
		echo "Error: podman is not installed or not in PATH"; \
		echo "Please install podman to use this target"; \
		echo "See: https://podman.io/getting-started/installation"; \
		exit 1; \
	fi
	./requirements/generate-build-requirements.sh

licenses:
	@echo "Syncing licenses/licenses.md..."
	@./sync-licenses.sh

check-licenses:
	@echo "Checking if licenses/licenses.md is in sync..."
	@make licenses
	@if ! git diff --quiet licenses/licenses.md; then \
		echo "licenses/licenses.md is out of sync. Run 'make licenses' to update it."; \
		git diff licenses/licenses.md; \
		exit 1; \
	else \
		echo "licenses/licenses.md is in sync."; \
	fi

.PHONY: docker-compose sync-requirements requirements requirements-check sync-build-tools licenses check-licenses
