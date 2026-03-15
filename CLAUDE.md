# Network Monitor — Project Context

## What this is
A Django-based network monitoring dashboard for the Schaff homelab. Monitors individual service health (not machine health) via TCP port checks and HTTP status checks. Also displays weather and Home Assistant data.

## Tech stack
- **Backend**: Django 5.1, Python 3.12
- **DB**: PostgreSQL
- **Background jobs**: Celery + Redis (60s polling cycle)
- **Auth**: django-auth-ldap → Active Directory (schaff.cc)
- **Frontend**: Django templates + HTMX + Bootstrap 5 (dark theme)

## Django apps
- `services/` — Service, Tag, ServiceStatus models; TCP/HTTP check logic; Celery tasks
- `integrations/` — SiteSettings singleton, weather.gov client, Home Assistant REST client, HAEntityConfig model
- `accounts/` — login/logout URLs (LDAP backend configured in settings.py)
- `dashboard/` — two views: read-only dashboard (`/`) and filterable monitor (`/monitor/`)

## Key models
- `services.Service` — name, host, port, check_type (tcp|http), http_url, tags (M2M), enabled, display_order
- `services.Tag` — free-text tags used for filtering on /monitor/
- `services.ServiceStatus` — per-check result: is_up, response_time_ms, detail. Last 1440 retained (24h at 1/min)
- `integrations.SiteSettings` — singleton: lat/lon for weather.gov, cached WFO grid (auto-resolved)
- `integrations.HAEntityConfig` — which HA entities appear on dashboard

## Infrastructure config
- **LDAP DC**: `castle.schaff.cc` / domain `schaff.cc`
- **LDAP bind account**: `svc_network-monitor-t0@schaff.cc` (password in .env as `LDAP_BIND_PASSWORD`)
- **AD group — login allowed**: `Schaff Users`
- **AD group — Django superuser**: `Service Admin`
- **Home Assistant**: `http://home.s1.schaff.cc:8123` (token in .env as `HA_TOKEN`)
- **Weather**: weather.gov (no API key), location set via SiteSettings admin (default: Madison WI, 43.0731, -89.4012)
- **All secrets**: stored in `.env` (see `.env.example`)

## Pages
- `/` — read-only wall-display dashboard: all services + weather widget + HA widgets. Auto-refreshes every 60s via HTMX.
- `/monitor/` — filterable view: filter by tag, status (up/down), or name search. HTMX-powered, no full page reloads.
- `/admin/` — Django admin: add/edit services, import HA entities, configure SiteSettings

## Deployment target
Ubuntu Server VM. See `deploy/INSTALL.md` for full setup steps.
Services: `netmon-gunicorn`, `netmon-celery-worker`, `netmon-celery-beat` (systemd units in `deploy/`)

## Working conventions
- Never hard-code secrets — always use `.env`
- Services are added via Django admin only — no code changes needed for new services
- HA entities are imported via the admin "Import from Home Assistant" action, then toggled per-entity
- Changing lat/lon in SiteSettings clears the cached weather grid automatically
- ServiceStatus history is pruned to 1440 records per service in the Celery task
