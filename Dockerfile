FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False \
    DEMO_MODE=False \
    DJANGO_ENABLE_HTTPS=True \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

WORKDIR /app

# A throwaway secret so `collectstatic` can run without DEBUG; the real key is
# injected at runtime via DJANGO_SECRET_KEY.
ARG DJANGO_SECRET_KEY=noop-build-secret

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY} python manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/login/ || exit 1

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]