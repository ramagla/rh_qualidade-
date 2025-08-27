import os
from pathlib import Path
from decouple import config
import platform

if platform.system() == "Windows":
    # No Windows apontamos para o Redis local
    CELERY_BROKER_URL = "redis://localhost:6379/0"
else:
    # Em Linux/produção também
    CELERY_BROKER_URL = "redis://localhost:6379/0"

import dj_database_url


# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

 # settings.py
BRASMOL_API_KEY = "78b04f986519f7300a7b96ed0990f7fd8d7399c3"  # sua chave fixa por ora
BRASMOL_BASE_URL = "https://app.cargamaquina.com.br/webservice/brasmol"


# URLs de redirecionamento
LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"

# Chave secreta e modo de depuração
SECRET_KEY = "-i@@0^twl)tb4ivcjrrt9mi5s)+ar@88ofqfmxav%7=4%v$z01"
DEBUG = True


GEMINI_API_KEY = config('GEMINI_API_KEY')


# Lista de hosts permitidos
ALLOWED_HOSTS = ["*", "192.168.0.139", "127.0.0.1", "localhost"]

# Link absoluto nos e-mails/alertas (usado pelas tasks do Celery)
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")

# Definição de aplicativos instalados
INSTALLED_APPS = [
    # Django apps (sempre primeiro)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps de terceiros
    "crispy_forms",
    "xhtml2pdf",
    "django_ckeditor_5",
    "widget_tweaks",
    "django_select2",
    "django_celery_beat",

    # Apps locais
    "Funcionario.apps.FuncionarioConfig",
    "core",
    "metrologia",
    "alerts",
    "qualidade_fornecimento",
    "portaria",
    "comercial",
    "assinatura_eletronica",
    "django.contrib.humanize",
    "tecnico",

]


DATE_FORMAT = "d 'de' F 'de' Y"


# Configurações do CKEditor
CRISPY_TEMPLATE_PACK = "bootstrap5"
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "subscript",
            "superscript",
            "|",
            "alignment:left",
            "alignment:center",
            "alignment:right",
            "alignment:justify",
            "|",
            "bulletedList",
            "numberedList",
            "outdent",
            "indent",
            "|",
            "link",
            "blockQuote",
            "imageUpload",
            "insertTable",
            "mediaEmbed",
            "|",
            "undo",
            "redo",
        ],
        "height": "300px",
        "width": "100%",
        "alignment": {"options": ["left", "center", "right", "justify"]},
        "image": {
            "toolbar": ["imageTextAlternative", "imageStyle:full", "imageStyle:side"]
        },
        "table": {"contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"]},
    },
}

# Middlewares
MIDDLEWARE = [
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # Certifique-se de que essa linha está presente
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.permission_middleware.PermissionMiddleware",
    
]

# Configuração de URLs e WSGI
ROOT_URLCONF = "rh_qualidade.urls"
WSGI_APPLICATION = "rh_qualidade.wsgi.application"

# Validação de senha
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalização
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Configurações Celery
CELERY_TASK_ALWAYS_EAGER = False
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = TIME_ZONE          # usa America/Sao_Paulo
CELERY_ENABLE_UTC = False            # executa no horário local
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
from kombu import Queue

# Fila padrão e roteamento para a fila de e-mails
CELERY_TASK_DEFAULT_QUEUE = "default"

CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("emails"),
    Queue("celery"),   # fila padrão do Celery (opcional, mas ajuda nos diagnósticos)
)

CELERY_TASK_ROUTES = {
    "alerts.tasks.send_email_async": {"queue": "emails"},
    "alerts.tasks.send_email_multipart_async": {"queue": "emails"},
}


# Evita o aviso do Celery 6 sobre retry no startup
broker_connection_retry_on_startup = True

# Configurações de arquivos estáticos e mídia
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Tipo de campo de chave primária padrão
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"


# Configurações de segurança
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

X_FRAME_OPTIONS = "ALLOWALL"
CSRF_TRUSTED_ORIGINS = [
    "https://qualidade.brasmol.com.br",
    "https://www.qualidade.brasmol.com.br",
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.0.139",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]



# Configurações de banco de dados
DATABASES = {
    "default": dj_database_url.config(
        default="postgres://postgres:gr212015@localhost:5432/rh_qualidade"
    )
}


# Sessões
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"

# Expiração automática da sessão após 20 minutos de inatividade
SESSION_COOKIE_AGE = 1200  # 20 minutos (em segundos)

# Renova o tempo de expiração a cada request — evita que a aba "travada" fique aberta indefinidamente
SESSION_SAVE_EVERY_REQUEST = True



# Configurações de templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.core_global_settings",
                "global_context_processors.global_menu",
                "rh_qualidade.context_processors.default_form", 
                'alerts.context_processors.alertas_do_usuario',

            ],
            "string_if_invalid": "",
        },
    },
]

# Caminho do diretório de logs
log_dir = os.path.join(BASE_DIR, "logs")

# Verificar se o diretório existe, se não, criar
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",         # só INFO+, não DEBUG
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(log_dir, "debug.log"),
            "level": "DEBUG",
            "encoding": "utf-8",     # aceita caracteres Unicode
        },
    },
    "loggers": {
        "django.template": {
            "handlers": ["console", "file"],
            "level": "INFO",         # sobe para INFO
            "propagate": False,
        },
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


# Configurações do e-mail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "webmail.c.inova.com.br"  # Substitua pelo host SMTP real
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "no-reply@brasmol.com.br"
EMAIL_HOST_PASSWORD = "Brasmol@2024"
DEFAULT_FROM_EMAIL = "no-reply@brasmol.com.br"
