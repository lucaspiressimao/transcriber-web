SERVER ?= $(DEPLOY_SERVER)
SERVER ?= root@111.222.333.444
DEST := /home
LOCAL_BASE := $(shell pwd)

run: build
	docker-compose up

build:
	docker-compose build --no-cache

up-build:
	docker-compose up --build
	
up: 
	docker-compose up

stop:
	docker-compose down

logs:
	docker-compose logs -f

psql:
	docker exec -it $$(docker-compose ps -q db) psql -U user -d transcriber


deploy-changes:
	@echo "🔍 Checking changes from last tag..."
	@FILES=$$(git diff --name-only $$(git describe --tags --abbrev=0)..HEAD); \
	if [ -z "$$FILES" ]; then \
		echo "✅ No changes"; \
	else \
		for f in $$FILES; do \
			echo "📤 Copiando $$f..."; \
			scp "$(LOCAL_BASE)/$$f" "$(SERVER):$(DEST)/$$f"; \
		done; \
		ssh $(SERVER) "cd $(DEST)/transcriber-web && docker compose down && docker compose up -d"; \
		echo "✅ Deploy done."; \
	fi