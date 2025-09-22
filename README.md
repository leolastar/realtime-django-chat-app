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

# Run it in docker locally

# 1. start application
cp .env.example .env
# add all the missing values with your own prefered values

# future work will be to add the migration during docker compose

# as of now update the database values and set

# HOST on line 107 for localhost

# 1 start the application with docker compose
docker compose up --build

# or

docker compose up --build -d

# 2. Run migrations & create superuser
python manage.py migrate
python manage.py createsuperuser

# 3 stope the application
docker compose down

# 4 update the HOST value on line 107 back to database

# 5 rstart the application
docker compose up --build

# or

docker compose up --build -d

# 6 start using the application  on locahost:8000


# happy chating
```
