#!/bin/bash
set -e

# Wait for database to be ready (with timeout)
echo "Waiting for database..."
timeout=60
counter=0

# Simple check: try to connect to database
if [ -n "$DB_HOST" ]; then
  DB_PORT=${DB_PORT:-5432}
  
  # First, wait for PostgreSQL to be ready using pg_isready (if available) or TCP connection
  echo "Checking PostgreSQL connectivity on ${DB_HOST}:${DB_PORT}..."
  
  # Try using pg_isready if postgresql-client is installed
  if command -v pg_isready > /dev/null 2>&1; then
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1 || [ $counter -eq $timeout ]; do
      echo "PostgreSQL is unavailable - sleeping ($counter/$timeout)"
      sleep 1
      counter=$((counter + 1))
    done
  else
    # Fallback: try TCP connection using nc (netcat) or timeout
    until (timeout 1 bash -c "cat < /dev/null > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null) || [ $counter -eq $timeout ]; do
      echo "Database connection unavailable - sleeping ($counter/$timeout)"
      sleep 1
      counter=$((counter + 1))
    done
  fi
  
  if [ $counter -eq $timeout ]; then
    echo "Warning: Database connection timeout after ${timeout} seconds!"
    echo "DB_HOST=${DB_HOST}, DB_PORT=${DB_PORT}, DB_NAME=${DB_NAME}, DB_USER=${DB_USER}"
    echo "Attempting to continue - migrations may fail if database is not ready..."
  else
    echo "Database is ready! Waiting 1 second for full initialization..."
    sleep 1
    echo "Database connection verified!"
  fi
else
  echo "No DB_HOST set, skipping database wait"
fi

# Run makemigrations (ignore errors if no changes)
echo "Running makemigrations..."
python manage.py makemigrations --noinput || echo "No new migrations needed"

# Run migrate
echo "Running migrate..."
python manage.py migrate --noinput

# Collect static files (only if STATIC_ROOT is configured)
if python -c "import django; django.setup(); from django.conf import settings; print(hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT)" 2>/dev/null | grep -q True; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput || echo "Static files collection skipped or completed"
else
    echo "STATIC_ROOT not configured, skipping static files collection"
fi

# Execute the main command
exec "$@"

