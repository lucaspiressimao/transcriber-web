run:
	docker-compose build --no-cache
	docker-compose up

stop:
	docker-compose down

logs:
	docker-compose logs -f

psql:
	docker exec -it $$(docker-compose ps -q db) psql -U user -d transcriber