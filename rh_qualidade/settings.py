import os
from pathlib import Path
import dj_database_url

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent



# URLs de redirecionamento
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/' 
LOGIN_REDIRECT_URL = '/' 

# Chave secreta e modo de depuração
SECRET_KEY = '-i@@0^twl)tb4ivcjrrt9mi5s)+ar@88ofqfmxav%7=4%v$z01'
DEBUG = True

# Lista de hosts permitidos
ALLOWED_HOSTS = ['*', '192.168.0.139', '127.0.0.1', 'localhost']

# Definição de aplicativos instalados
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "Funcionario",
    'metrologia',
    'crispy_forms',
    'xhtml2pdf',
    'django_ckeditor_5',
    'widget_tweaks',
    'django_select2',
    'ckeditor',
    'ckeditor_uploader',
    'django_celery_beat',
    'alerts',

]
    
DATE_FORMAT = "d 'de' F 'de' Y"

# Configurações Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'



# Configurações do CKEditor
CRISPY_TEMPLATE_PACK = 'bootstrap5'
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',  # Define a toolbar completa
        'height': 300,
        'width': '100%',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Image', 'Table', 'HorizontalRule', 'SpecialChar'],
            ['Undo', 'Redo'],
            ['Format', 'Font', 'FontSize'],
        ],
    },
}

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', '|',
            'alignment:left', 'alignment:center', 'alignment:right', 'alignment:justify', '|',
            'bulletedList', 'numberedList', 'outdent', 'indent', '|',
            'link', 'blockQuote', 'imageUpload', 'insertTable', 'mediaEmbed', '|',
            'undo', 'redo'
        ],
        'height': '300px',
        'width': '100%',
        'alignment': {
            'options': ['left', 'center', 'right', 'justify']
        },
        'image': {
            'toolbar': ['imageTextAlternative', 'imageStyle:full', 'imageStyle:side']
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells']
        },
    },
}

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Certifique-se de que essa linha está presente
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rh_qualidade.middleware.PermissionMiddleware',

]

# Configuração de URLs e WSGI
ROOT_URLCONF = "rh_qualidade.urls"
WSGI_APPLICATION = "rh_qualidade.wsgi.application"

# Validação de senha
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Configurações de arquivos estáticos e mídia
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'Funcionario' / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Tipo de campo de chave primária padrão
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'



# Configurações de segurança
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = False
X_FRAME_OPTIONS = 'ALLOWALL'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost', 
    'http://127.0.0.1', 
    'http://192.168.0.139'
]


# Configurações de banco de dados
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://postgres:gr212015@localhost:5432/rh_qualidade'
    )
}




# Sessões
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"

# Configurações de templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'Funcionario.context_processors.global_settings',
                'global_context_processors.global_menu',

            ],
        },
    },
]

# Caminho do diretório de logs
log_dir = os.path.join(BASE_DIR, 'logs')

# Verificar se o diretório existe, se não, criar
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(log_dir, 'debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configurações do e-mail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'webmail.c.inova.com.br'  # Substitua pelo host SMTP real
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'no-reply@brasmol.com.br'
EMAIL_HOST_PASSWORD = 'Brasmol@2024'
DEFAULT_FROM_EMAIL = 'no-reply@brasmol.com.br'
