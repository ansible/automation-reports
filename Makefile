# If you are running an old version, you might need docker-compose instead
DOCKER_COMPOSE?=docker compose

docker-compose:
	$(DOCKER_COMPOSE) --file compose/compose.yml up

# Requirements management
sync-requirements:
	@echo "Syncing requirements files from requirements.txt..."
	./sync-requirements.sh

requirements: sync-requirements

requirements-check:
	@echo "Checking if requirements files are in sync..."
	@./sync-requirements.sh
	@if ! git diff --quiet requirements-pinned.txt requirements-build.txt; then \
		echo "Requirements files are out of sync. Run 'make sync-requirements' to update them."; \
		git diff requirements-pinned.txt requirements-build.txt; \
		exit 1; \
	else \
		echo "Requirements files are in sync."; \
	fi

.PHONY: sync-requirements requirements requirements-check
