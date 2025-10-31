FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script early (for better caching)
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Copy project
COPY . /app/

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]
