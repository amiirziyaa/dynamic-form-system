# Docker Setup for Dynamic Form System

This project is containerized with Docker and Docker Compose to provide a consistent development and testing environment with all required dependencies (PostgreSQL, Redis, Celery).

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

### 1. Create `.env` file

Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=dynamicformdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5433
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

**Note**: Ports shown above (5433, 6380) are host ports. Inside Docker containers, services use standard ports (5432, 6379).

### 2. Build and Start Services

```bash
# Build containers
make build

# Start all services
make up

# View logs
make logs
```

Or using Docker Compose directly:

```bash
docker-compose build
docker-compose up -d
```

### 3. Run Migrations

```bash
make migrate
# or
docker-compose exec web python manage.py migrate
```

### 4. Create Superuser

```bash
make createsuperuser
# or
docker-compose exec web python manage.py createsuperuser
```

## Services

The Docker Compose setup includes:

- **web**: Django application (Daphne ASGI server)
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **celery**: Celery worker for background tasks
- **celery-beat**: Celery beat scheduler for periodic tasks

## Running Tests

### All Tests

```bash
make test-all
# or
docker-compose -f docker-compose.test.yml run --rm test python manage.py test --keepdb --verbosity=2
```

### Specific Test Module

```bash
make test-specific TEST=notifications.test_admin_endpoints
# or
docker-compose -f docker-compose.test.yml run --rm test python manage.py test notifications.test_admin_endpoints --keepdb --verbosity=2
```

### Admin Endpoints and WebSocket Tests

```bash
make test-admin-websocket
# or
docker-compose -f docker-compose.test.yml run --rm test python manage.py test notifications.test_admin_endpoints analytics.test_websocket --keepdb --verbosity=2
```

## Makefile Commands

```bash
make build          # Build Docker images
make up             # Start all services
make down           # Stop all services
make logs           # View logs
make test           # Run all tests
make test-specific  # Run specific test (TEST=module.path)
make test-all       # Run all tests
make shell          # Django shell
make migrate        # Run migrations
make makemigrations # Create migrations
make createsuperuser # Create superuser
make collectstatic  # Collect static files
make restart        # Restart services
make clean          # Remove containers and volumes
```

## Accessing Services

- **Web Application**: http://localhost:8001
- **API Docs (Swagger)**: http://localhost:8001/api/v1/swagger/
- **API Docs (ReDoc)**: http://localhost:8001/api/v1/redoc/
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

**Note**: These ports are configured to avoid conflicts with system-wide applications. You can change them in `.env` file if needed.

## Development Workflow

1. **Start services**: `make up`
2. **Run migrations**: `make migrate`
3. **Create superuser** (first time): `make createsuperuser`
4. **View logs**: `make logs`
5. **Run tests**: `make test-all`
6. **Stop services**: `make down`

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Check that the `db` service is running: `docker-compose ps`
2. Wait for database to be ready: `docker-compose logs db`
3. Verify environment variables in `.env` file

### Redis Connection Issues

If Celery or WebSocket connections fail:

1. Check that Redis is running: `docker-compose ps`
2. Verify `REDIS_URL` in `.env`
3. Check Redis logs: `docker-compose logs redis`

### Port Conflicts

The default ports are set to avoid conflicts:
- **Web**: 8001 (instead of 8000)
- **PostgreSQL**: 5433 (instead of 5432)
- **Redis**: 6380 (instead of 6379)

If these are still in use, update `docker-compose.yml` or set environment variables in `.env`:

```env
WEB_PORT=8002
DB_PORT=5434
REDIS_PORT=6381
```

### Clean Start

To start fresh (removes all data):

```bash
make clean
make build
make up
make migrate
```

## Production Notes

For production:

1. Use environment-specific `.env` files
2. Set `DEBUG=False`
3. Use strong `SECRET_KEY`
4. Configure proper database credentials
5. Set up SSL/TLS
6. Configure proper CORS and allowed hosts
7. Use external PostgreSQL and Redis services
8. Set up proper backup strategies

