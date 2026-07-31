<!-- # JMCFI AMS — Accreditation Portal (UI scaffold)

Django project reproducing the AMS dashboard UI. This is the front-end
shell only — no auth, no models, no real data yet — built so features
can be added app-by-app without restructuring later.

## Structure

```
config/            project settings, root urls.py
core/               shared nav data (context_processors.py), icon set
                     & active-link template tags, notifications stub
dashboard/          main dashboard: KPIs, AI alert, trend + readiness charts
accreditation/      Levels & Areas / Submission Workspace / Review Workflow (stubs)
resources/          Document Repository / Communication (stubs)
intelligence/       Reports & Monitoring / Smart Companion (stubs)
accounts/           User Management / Settings & Profile (stubs)
templates/          base.html + shared partials (sidebar, topbar, placeholder)
static/css/         tokens.css (design tokens) → base.css → layout.css → dashboard.css
```

Each app owns its own `urls.py`, `views.py`, and `templates/<app_name>/`
directory (Django's namespaced-template convention), so templates never
collide as the project grows.

The sidebar navigation is defined once, in `core/context_processors.py`,
and rendered from that data in every template — add a nav item there
and it appears (with correct active-state highlighting) everywhere.

## Run it

```
pip install django
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/ -->
