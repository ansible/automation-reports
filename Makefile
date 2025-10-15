# If you are running an old version, you might need docker-compose instead
DOCKER_COMPOSE?=docker compose

docker-compose:
	$(DOCKER_COMPOSE) --file compose/compose.yml up

# Requirements management
sync-requirements:
	@echo "Syncing requirements-build.txt from requirements-pinned.txt..."
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
		./sync-requirements.sh

requirements: sync-requirements

requirements-check:
	@echo "Checking if requirements-build.txt is in sync..."
	@make sync-requirements
	@if ! git diff --quiet requirements-build.txt; then \
		echo "Requirements-build.txt is out of sync. Run 'make sync-requirements' to update it."; \
		git diff requirements-build.txt; \
		exit 1; \
	else \
		echo "Requirements-build.txt is in sync."; \
	fi

.PHONY: sync-requirements requirements requirements-check
