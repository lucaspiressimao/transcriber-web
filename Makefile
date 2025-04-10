run: build
	docker-compose -f docker-compose-local.yml up

build:
	docker-compose -f docker-compose-local.yml build --no-cache

up-build:
	docker-compose -f docker-compose-local.yml up --build
	
up: 
	docker-compose -f docker-compose-local.yml up

stop:
	docker-compose -f docker-compose-local.yml down

logs:
	docker-compose -f docker-compose-local.yml logs -f

psql:
	docker exec -it $$(docker-compose ps -q db) psql -U user -d transcriber