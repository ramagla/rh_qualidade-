import os
from pathlib import Path
import dj_database_url

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# URLs de redirecionamento
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

# Chave secreta deve ser definida por ambiente (ver development.py e production.py)
SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_desenvolvimento')

# Lista de hosts permitidos será configurada em cada ambiente
ALLOWED_HOSTS = []

# Definição de aplicativos instalados
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "Funcionario",
    'widget_tweaks',
    'crispy_forms',  
    'xhtml2pdf', 
    'django_ckeditor_5' 
]

# Configurações do CKEditor
CRISPY_TEMPLATE_PACK = 'bootstrap5'
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
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
