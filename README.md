# Django Real‑Time Chat

- **Python 3.12** / **Django 4.2+**
- **Channels** + **Daphne** (WebSocket layer)
- **Redis** (message store + channel layer)
- **PostgreSQL** (user & conversation metadata)
- **JWT** authentication (`djangorestframework-simplejwt`)
- **Prometheus** metrics
- **Docker** + **docker‑compose**
- **GitHub Actions** CI

## Features

| Feature               | Implementation                                |
| --------------------- | --------------------------------------------- |
| Real‑time messaging   | Channels + WebSockets                         |
| Message persistence   | Redis list per conversation                   |
| User & convo metadata | PostgreSQL                                    |
| Throttling            | 1 msg / sec per user + per conversation       |
| Logging               | Structured JSON to stdout (Docker compatible) |
| Monitoring            | `/metrics` exposed for Prometheus             |
| Tests                 | Unit & integration tests                      |
| CI                    | GitHub Actions workflow                       |
| Docker                | `docker compose up`                           |

## Getting Started

```bash
git clone
cd

# Run Locally

# 1. Install dependencies
pip install -r requirements-dev.txt

# 2. Run migrations & create superuser
python manage.py migrate
python manage.py createsuperuser

# 3. Run the dev server
python manage.py runserver

# Run it in docker locally

# 1. start application
cp .env.example .env
docker compose up --build

# 2. Run migrations & create superuser
python manage.py migrate
python manage.py createsuperuser
```
