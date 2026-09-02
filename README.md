# JMCFI AMS

Internal accreditation evidence management system built with Django and SQLite for development.

## Run locally

```bash
./.venv/bin/python manage.py migrate
DEMO_MODE=True ./.venv/bin/python manage.py seed_demo
DEMO_MODE=True ./.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/login/>.

`seed_demo` is available only when `DEMO_MODE` is enabled (enabled by default while `DEBUG=True`). It creates internal demo accounts for Superadmin, Admin, QA, Accreditation Head, Program Head, Dean, and Area Chair. Their development password is `123`, and first-login password changes are currently disabled. Set `DEBUG=False` or `DEMO_MODE=False` in production so demo seeding and demo authentication are disabled.

## Workflow

Evidence is stored as Cycle → Level → Area → Sub-area → Requirement → Submission. Program Heads create versions and supporting files, then submissions move through Dean, Area Chair, and QA/Accreditation Head review. Revision requests retain the reviewer, remarks, files, versions, comments, notifications, and audit records.

All important workflow data is stored in the database. Browser local storage is not used for evidence, submissions, approvals, or review decisions.

## Configuration

Settings are read from `.env` (see `.env.example`). Copy the example and fill in values:

```bash
cp .env.example .env
```

Required in production:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Boot refusal to start without it when `DEBUG=False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DEBUG` | Keep `False` in production |
| `DEMO_MODE` | Keep `False` to disable demo accounts/default auth |
| `DJANGO_ENABLE_HTTPS` | Enables `SECURE_SSL_REDIRECT`/HSTS/secure cookies |

Optional:

- Database — defaults to SQLite. Switch to PostgreSQL via `DJANGO_DB_ENGINE`, `DJANGO_DB_NAME/USER/PASSWORD/HOST/PORT`. Pin `psycopg[binary]` in `requirements.txt`.
- Cache/sessions over Redis — `DJANGO_CACHE_BACKEND=django_redis.cache.RedisCache` and `DJANGO_CACHE_LOCATION=redis://redis:6379/1`; pin `django-redis`.
- AI provider — the AVA assistant (AI Insights) answers from the live database out of the box. To use an OpenAI-compatible provider, set `AI_BASE_URL`, `AI_API_KEY`, and optionally `AI_MODEL` (`gpt-4o-mini` default) and `AI_TIMEOUT`/`AI_MAX_TOKENS`. Without a provider it always falls back to deterministic, DB-grounded answers.

## Deployment (Docker)

```bash
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
export DJANGO_ALLOWED_HOSTS=ams.example.edu
export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(30))')"
docker compose up -d --build
```

The compose stack runs Postgres, Redis, and the web app behind gunicorn. Apply migrations and create an admin in the running web container:

```bash
docker compose exec web python manage.py createsuperuser
```

## CI/CD + DevSecOps

`.github/workflows/ci.yml` runs on every push/PR to `main`:

- **Lint** — flake8
- **SAST** — bandit (static) + `pip-audit` (dependency vulnerabilities)
- **Tests** — `manage.py check` and the full test suite
- **DAST** — OWASP ZAP baseline scan of a seeded, running instance; reports uploaded as artifacts
- **Collect static** — validated at image build

`.github/workflows/deploy.yml` builds and pushes the image to GHCR, then deploys over SSH to a host using `SERVER_HOST`, `SERVER_USER`, and `SSH_PRIVATE_KEY` secrets. `sonar-project.properties` configures SonarQube for server-side analysis. The final gate is a zero-finding `pip-audit` run against `requirements.txt`.

## Security & data protection

- Session auth with an 8-hour timeout; browsers close sessions unless `DEBUG`.
- Rate limiting on AVA assistant and messaging endpoints.
- Audit log for login, registration, role, password, and workflow events.
- Error pages hide stack traces; emails of failures go to `mail_admins` (configure `ADMINS`).
- File uploads capped at 5 MB; `SECURE_REFERRER_POLICY`, HttpOnly CSRF, and HTTPS/HSTS settings applied.

## Quality checks

```bash
python -m flake8 config core accounts accreditation resources intelligence dashboard
python -m bandit -r config core accounts accreditation resources intelligence dashboard
python -m pip_audit -r requirements.txt
python manage.py test
```
