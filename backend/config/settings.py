import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    "apps.agent",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

# ── Databases ───────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "kfueit_agent"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# LMS MySQL connection — only active in production when USE_DUMMY_DATA=False
USE_DUMMY_DATA = os.getenv("USE_DUMMY_DATA", "True") == "True"

if not USE_DUMMY_DATA:
    DATABASES["lms"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("LMS_DB_NAME", ""),
        "USER": os.getenv("LMS_DB_USER", ""),
        "PASSWORD": os.getenv("LMS_DB_PASSWORD", ""),
        "HOST": os.getenv("LMS_DB_HOST", ""),
        "PORT": os.getenv("LMS_DB_PORT", "3306"),
        "OPTIONS": {"read_default_file": "/etc/mysql/my.cnf"},
    }

# ── OpenAI ───────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")

# ── Pinecone ─────────────────────────────────────────────────────────────────

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "kfueit-agent")
PINECONE_HOST = os.getenv("PINECONE_HOST", "")
PINECONE_CONTROL_PLANE_URL = os.getenv("PINECONE_CONTROL_PLANE_URL", "https://api.pinecone.io")
PINECONE_API_VERSION = os.getenv("PINECONE_API_VERSION", "2025-10")
PINECONE_EMBEDDING_MODEL = os.getenv("PINECONE_EMBEDDING_MODEL", "multilingual-e5-large")
PINECONE_TEXT_FIELD = os.getenv("PINECONE_TEXT_FIELD", "text")
PINECONE_SEARCH_INPUT_FIELD = os.getenv("PINECONE_SEARCH_INPUT_FIELD", "text")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "kfueit_public")
PINECONE_PUBLIC_NAMESPACE = os.getenv("PINECONE_PUBLIC_NAMESPACE", PINECONE_NAMESPACE)
PINECONE_ENABLE_PUBLIC_FALLBACK = os.getenv("PINECONE_ENABLE_PUBLIC_FALLBACK", "True") == "True"
PINECONE_REQUIRE_STUDENT_NAMESPACE_FOR_RAG = (
    os.getenv("PINECONE_REQUIRE_STUDENT_NAMESPACE_FOR_RAG", "True") == "True"
)


def _require_env(name: str, value: str):
    if not value:
        raise ImproperlyConfigured(f"Required environment variable '{name}' is missing.")


def _validate_secret_settings():
    _require_env("SECRET_KEY", SECRET_KEY)
    _require_env("OPENAI_API_KEY", OPENAI_API_KEY)
    _require_env("OPENAI_LLM_MODEL", OPENAI_LLM_MODEL)

    if PINECONE_API_KEY:
        _require_env("PINECONE_API_KEY", PINECONE_API_KEY)
        _require_env("PINECONE_INDEX_NAME", PINECONE_INDEX_NAME)


_validate_secret_settings()

# ── Celery + Redis (disabled on Vercel serverless) ───────────────────────────

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = os.getenv("VERCEL", "") != ""  # run tasks synchronously on Vercel

# ── n8n Webhook URLs ──────────────────────────────────────────────────────────

N8N_WEBHOOK_SEND_EMAIL = os.getenv("N8N_WEBHOOK_SEND_EMAIL", "http://localhost:5678/webhook/send-email")
N8N_WEBHOOK_LOG_COMPLAINT = os.getenv("N8N_WEBHOOK_LOG_COMPLAINT", "http://localhost:5678/webhook/log-complaint")
N8N_WEBHOOK_ESCALATE = os.getenv("N8N_WEBHOOK_ESCALATE", "http://localhost:5678/webhook/escalate")

# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True

# ── Static ────────────────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True
