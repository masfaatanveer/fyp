from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-kfueit-dev-key-change-in-production-2024"
DEBUG = False
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

# ── Database (Supabase) ───────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres.lsfluvxczrwbecljinbr",
        "PASSWORD": "(Masfa2779)",
        "HOST": "aws-1-ap-northeast-1.pooler.supabase.com",
        "PORT": "5432",
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"sslmode": "require"},
    }
}

USE_DUMMY_DATA = True

# ── OpenAI ────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = "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"
OPENAI_LLM_MODEL = "gpt-4.1-mini"

# ── Pinecone ──────────────────────────────────────────────────────────────────

PINECONE_API_KEY = "pcsk_6X7jyt_Fi8k4Cvy1pgRReF6qeBY1hxLNvbLFuDc4scMWiZSGQUrWdsVGgqYCmtbWGxoYzV"
PINECONE_INDEX_NAME = "kfueit-fyp"
PINECONE_HOST = "kfueit-fyp-0rtuydk.svc.aped-4627-b74a.pinecone.io"
PINECONE_CONTROL_PLANE_URL = "https://api.pinecone.io"
PINECONE_API_VERSION = "2025-10"
PINECONE_EMBEDDING_MODEL = "multilingual-e5-large"
PINECONE_TEXT_FIELD = "text"
PINECONE_SEARCH_INPUT_FIELD = "text"
PINECONE_NAMESPACE = "kfueit_public"
PINECONE_PUBLIC_NAMESPACE = "kfueit_public"
PINECONE_ENABLE_PUBLIC_FALLBACK = True
PINECONE_REQUIRE_STUDENT_NAMESPACE_FOR_RAG = True

# ── Celery ────────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = True

# ── n8n Webhooks ──────────────────────────────────────────────────────────────

N8N_WEBHOOK_SEND_EMAIL = "http://localhost:5678/webhook/send-email"
N8N_WEBHOOK_LOG_COMPLAINT = "http://localhost:5678/webhook/log-complaint"
N8N_WEBHOOK_ESCALATE = "http://localhost:5678/webhook/escalate"

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
