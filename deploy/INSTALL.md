# Installation Guide — Network Monitor

Target OS: Ubuntu Server 24.04 LTS

## 1. System packages

```bash
sudo apt update && sudo apt install -y \
    python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server nginx \
    libldap2-dev libsasl2-dev libssl-dev \
    python3-dev build-essential
```

## 2. Create service user and app directory

```bash
sudo useradd --system --home /opt/network_dashboard --shell /bin/bash netmon
sudo mkdir -p /opt/network_dashboard
sudo chown netmon:netmon /opt/network_dashboard
```

## 3. Copy application files

Copy the contents of this repository to `/opt/network_dashboard/`:

```bash
sudo cp -r . /opt/network_dashboard/
sudo chown -R netmon:netmon /opt/network_dashboard/
```

## 4. Python virtual environment

```bash
sudo -u netmon python3.12 -m venv /opt/network_dashboard/venv
sudo -u netmon /opt/network_dashboard/venv/bin/pip install -r /opt/network_dashboard/requirements.txt
```

## 5. PostgreSQL database

```bash
sudo -u postgres psql <<EOF
CREATE USER netmon WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE network_dashboard OWNER netmon;
EOF
```

## 6. Environment file

```bash
sudo -u netmon cp /opt/network_dashboard/.env.example /opt/network_dashboard/.env
sudo -u netmon nano /opt/network_dashboard/.env
```

Fill in:
- `SECRET_KEY` — generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DATABASE_URL` — e.g. `postgres://netmon:choose-a-strong-password@localhost:5432/network_dashboard`
- `LDAP_BIND_PASSWORD` — password for `svc_network-monitor-t0`
- `HA_TOKEN` — Home Assistant Long-Lived Access Token
- `ALLOWED_HOSTS` — your server hostname(s)

## 7. Django setup

```bash
cd /opt/network_dashboard
sudo -u netmon venv/bin/python manage.py migrate
sudo -u netmon venv/bin/python manage.py collectstatic --noinput
```

## 8. Systemd services

```bash
sudo cp deploy/gunicorn.service     /etc/systemd/system/netmon-gunicorn.service
sudo cp deploy/celery-worker.service /etc/systemd/system/netmon-celery-worker.service
sudo cp deploy/celery-beat.service   /etc/systemd/system/netmon-celery-beat.service

sudo systemctl daemon-reload
sudo systemctl enable --now redis-server
sudo systemctl enable --now netmon-gunicorn
sudo systemctl enable --now netmon-celery-worker
sudo systemctl enable --now netmon-celery-beat
```

## 9. Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/network-monitor
sudo ln -s /etc/nginx/sites-available/network-monitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Place your TLS certificate and key at:
- `/etc/ssl/certs/monitor.schaff.cc.crt`
- `/etc/ssl/private/monitor.schaff.cc.key`

If you use Let's Encrypt via certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d monitor.schaff.cc
```

## 10. First run — add services

1. Navigate to `https://monitor.schaff.cc/admin/`
2. Log in with your AD credentials (must be in `Service Admin` group)
3. Go to **Site Settings** → set your lat/lon if not in Madison, WI
4. Go to **Home Assistant Entities** → use the "Import from Home Assistant" action → enable the ones you want
5. Go to **Services** → add your first service
6. The Celery beat scheduler will run the first check within 60 seconds

## LDAP notes

- Bind account: `svc_network-monitor-t0@schaff.cc`
- Users must be in `Schaff Users` group to log in
- Users in `Service Admin` group get Django staff + superuser access
- The bind account only needs read access to AD (no write permissions needed)

## Troubleshooting

```bash
# Check gunicorn logs
sudo journalctl -u netmon-gunicorn -f

# Check celery worker logs
sudo journalctl -u netmon-celery-worker -f

# Check celery beat logs
sudo journalctl -u netmon-celery-beat -f

# Test LDAP connectivity
ldapsearch -H ldap://castle.schaff.cc \
  -D "CN=svc_network-monitor-t0,CN=Users,DC=schaff,DC=cc" \
  -W -b "DC=schaff,DC=cc" "(sAMAccountName=yourusername)"
```
