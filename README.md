# JMCFI AMS

Internal accreditation evidence management system built with Django and SQLite for development.

## Run locally

```bash
./.venv/bin/python manage.py migrate
DEMO_MODE=True ./.venv/bin/python manage.py seed_demo
DEMO_MODE=True ./.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/login/>.

`seed_demo` is available only when `DEMO_MODE` is enabled (enabled by default while `DEBUG=True`). It creates internal demo accounts for Superadmin, Admin, QA, Accreditation Head, Program Head, Dean, and Area Chair. Their development password is `123`; every demo account is marked to require a password change. Set `DEBUG=False` or `DEMO_MODE=False` in production so demo seeding and demo authentication are disabled.

## Workflow

Evidence is stored as Cycle → Level → Area → Sub-area → Requirement → Submission. Program Heads create versions and supporting files, then submissions move through Dean, Area Chair, and QA/Accreditation Head review. Revision requests retain the reviewer, remarks, files, versions, comments, notifications, and audit records.

All important workflow data is stored in the database. Browser local storage is not used for evidence, submissions, approvals, or review decisions.
