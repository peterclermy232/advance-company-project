FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy project
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Collect static files (will use environment variables at runtime)
RUN python manage.py collectstatic --noinput --clear || true

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD python manage.py migrate --noinput && \
    python manage.py create_admin && \
    gunicorn advance_company.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3