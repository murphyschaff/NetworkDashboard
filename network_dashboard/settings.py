import environ
import ldap
from django_auth_ldap.config import LDAPSearch, ActiveDirectoryGroupType

BASE_DIR = environ.Path(__file__) - 2

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR(".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "solo",
    "services",
    "integrations",
    "accounts",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "network_dashboard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR("templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "network_dashboard.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULE = {
    "check-all-services": {
        "task": "services.tasks.check_all_services",
        "schedule": 60.0,  # every 60 seconds
    },
    "refresh-weather": {
        "task": "integrations.tasks.refresh_weather",
        "schedule": 600.0,  # every 10 minutes
    },
    "refresh-ha-states": {
        "task": "integrations.tasks.refresh_ha_states",
        "schedule": 60.0,  # every 60 seconds
    },
}
CELERY_TIMEZONE = "America/Chicago"

# Auth
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_LDAP_SERVER_URI = env("LDAP_SERVER_URI")
AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}
AUTH_LDAP_BIND_DN = env("LDAP_BIND_DN")
AUTH_LDAP_BIND_PASSWORD = env("LDAP_BIND_PASSWORD")

_ldap_base_dn = env("LDAP_BASE_DN")
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    _ldap_base_dn,
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)",
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    _ldap_base_dn,
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)",
)
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

AUTH_LDAP_REQUIRE_GROUP = env("LDAP_REQUIRE_GROUP")

_ldap_admin_group = env("LDAP_ADMIN_GROUP")
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff": _ldap_admin_group,
    "is_superuser": _ldap_admin_group,
}

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_CACHE_TIMEOUT = 0

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Reverse proxy (Nginx Proxy Manager)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR("staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django_auth_ldap": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}

# Home Assistant
HA_BASE_URL = "http://home.s1.schaff.cc:8123"
HA_TOKEN = env("HA_TOKEN", default="")
