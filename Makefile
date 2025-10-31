.PHONY: build up down test test-specific logs shell migrate makemigrations

# Build containers
build:
	docker compose build

# Build containers with retry (for network issues)
build-retry:
	@echo "Attempting to build with retries..."
	@for i in 1 2 3; do \
		echo "Build attempt $$i..."; \
		docker compose build && break || sleep 5; \
	done

# Build containers without pulling (use cached images)
build-no-pull:
	docker compose build --pull=never

# Start services
up:
	docker compose up -d

# Stop services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Build test image
build-test:
	docker compose -f docker-compose.test.yml build test

# Run tests
test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run specific test
test-specific:
	docker compose -f docker-compose.test.yml run --rm test python manage.py test $(TEST) --keepdb --verbosity=2

# Run tests for admin endpoints and websocket
test-admin-websocket:
	docker compose -f docker-compose.test.yml build test
	docker compose -f docker-compose.test.yml run --rm test python manage.py test notifications.test_admin_endpoints analytics.test_websocket --keepdb --verbosity=2

# Run all tests (rebuilds image to ensure dependencies are up to date)
test-all:
	docker compose -f docker-compose.test.yml build test
	docker compose -f docker-compose.test.yml run --rm test python manage.py test --keepdb --verbosity=2

# Django shell
shell:
	docker compose exec web python manage.py shell

# Database migrations
migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

# Create superuser
createsuperuser:
	docker compose exec web python manage.py createsuperuser

# Collect static files
collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# Restart services
restart:
	docker compose restart

# Clean up (remove containers, volumes)
clean:
	docker compose down -v
	docker compose -f docker-compose.test.yml down -v

