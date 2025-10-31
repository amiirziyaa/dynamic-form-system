# Docker Setup - Port Configuration

## Default Ports (Non-Standard to Avoid Conflicts)

The project uses non-standard ports to avoid conflicts with system-wide applications:

### Main Services (`docker-compose.yml`)
- **Web Application**: `8001` (instead of 8000)
- **PostgreSQL**: `5433` (instead of 5432)  
- **Redis**: `6380` (instead of 6379)

### Test Services (`docker-compose.test.yml`)
- **PostgreSQL**: `5434` (test database)
- **Redis**: `6381` (test cache/broker)

## Environment Variables

If you have a `.env` file, make sure it uses the correct ports:

```env
DB_PORT=5433          # Not 5432!
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/2
```

**Important**: 
- `DB_PORT` in `.env` should be `5433` (not 5432)
- `REDIS_URL` should use port `6380` when connecting from host
- Inside Docker containers, services still use standard ports (5432, 6379)

## Changing Ports

If you need to use different ports, you can set them in your `.env` file:

```env
WEB_PORT=8002
DB_PORT=5435
REDIS_PORT=6382
```

Then the docker-compose files will use these values.

## Verifying Ports

Check which ports are actually being used:

```bash
docker compose config | grep published
# or
docker compose ps
```

## Common Issues

### Port Already in Use

If you see errors like "address already in use":
1. Check if you have a `.env` file with old port values
2. Update `.env` to use the new ports (5433, 6380, 8001)
3. Stop any conflicting containers: `docker compose down`
4. Restart: `docker compose up -d`

### Old Containers Still Running

Clean up everything:
```bash
docker compose down -v
# Then restart
docker compose up -d
```

