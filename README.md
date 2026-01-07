# Dean's Crisis Management System - API

A Django-based REST API for the Dean's Crisis Management System.

---

## Table of Contents
- [Setup Environment](#setup-environment)
- [Environment Variables](#environment-variables)
- [Run Server](#run-server)
- [Useful Commands](#useful-commands)
- [API Configuration](#api-configuration)

---

# Setup Environment

## On *nix

1. Install `docker` and `docker-compose` correctly.

[How to install on mac](http://sourabhbajaj.com/mac-setup/Docker/)

2. Setup python
```shell
$ virtualenv -p python3 env 
$ source env/bin/activate
$ pip install -r requirements.txt
```

## On Windows
```shell
# Install Docker Desktop for Windows
# Then run:
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

---

# Environment Variables

This application uses environment variables for configuration. Copy `.env.example` to `.env` and customize for your environment.

```shell
cp .env.example .env
```

## Required Variables

| Variable | Description | Default | Required in Production |
|----------|-------------|---------|----------------------|
| `DJANGO_SECRET_KEY` | Django secret key for cryptographic signing | *dev fallback* | ⚠️ **YES** |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `*` | ⚠️ **YES** |
| `PRODUCTION` | Set to `1` for production mode | `0` | YES |

## Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `IN_DOCKER` | Set to `1` when running in Docker | `0` |
| `POSTGRES_DB` | PostgreSQL database name | `deans_db` |
| `POSTGRES_USER` | PostgreSQL username | `deans_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `deans_password` |
| `POSTGRES_HOST` | PostgreSQL host | `db` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_CONN_MAX_AGE` | Connection pool max age (seconds) | `60` |
| `POSTGRES_CONNECT_TIMEOUT` | Connection timeout (seconds) | `10` |

## CORS Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000` |

## API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PAGE_SIZE` | Default pagination page size | `20` |
| `API_THROTTLE_ANON` | Rate limit for anonymous users | `100/hour` |
| `API_THROTTLE_USER` | Rate limit for authenticated users | `1000/hour` |

## Security Configuration (Production)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `true` |
| `SECURE_HSTS_SECONDS` | HSTS max-age in seconds | `31536000` |

## Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `DJANGO_LOG_DIR` | Directory for log files | `./logs` |

## Redis / Channel Layers

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis host for Django Channels | `redis` |
| `REDIS_PORT` | Redis port | `6379` |

### Generating a Secret Key

For production, generate a secure secret key:
```shell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

# Run Server

If on Mac or Windows the container will run on Docker Machine which is a virtual machine, and will have its own IP address. You could run `docker-machine ip` to check the address, and such address will be used to access the front end. However, on Linux, you could simply access `localhost`.

## Using Docker Compose

```shell
# Development
docker-compose up

# Production (with environment variables)
PRODUCTION=1 DJANGO_SECRET_KEY=your-secret-key docker-compose up
```

## On Windows

```shell
docker-compose up
```

---

# Useful Commands

## Django Migration

```shell
docker-compose run web python manage.py migrate
```

## Create Superuser

```shell
docker-compose run web python manage.py createsuperuser
```

## Run Tests

```shell
docker-compose run web python manage.py test
```

## View Logs

```shell
# Container logs
docker-compose logs -f web

# Application logs (if DJANGO_LOG_DIR is set)
tail -f logs/django.log
```

---

# API Configuration

## Pagination

API responses are paginated by default. Control pagination with:
- `API_PAGE_SIZE` environment variable (default: 20)
- Query parameter: `?page=2`

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

Configure via `API_THROTTLE_ANON` and `API_THROTTLE_USER` environment variables.

## Security Headers (Production)

When `PRODUCTION=1`, the following security features are enabled:
- HTTPS redirect
- Secure cookies (session & CSRF)
- HSTS (HTTP Strict Transport Security)
- XSS protection
- Content-Type nosniff

---

# TODO

- [ ] persist data in a dockerized postgres database using volumes
- [ ] django-restful doc
- [ ] remove 'ADD' on setting page 
