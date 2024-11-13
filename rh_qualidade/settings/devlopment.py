from .base import *

# Ativar modo de depuração
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Configuração do banco de dados para desenvolvimento
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Definir uma chave secreta para o ambiente de desenvolvimento (opcional)
SECRET_KEY = "django-insecure-$-(!3b#gn3ut1k&q12b%x2zfi=sqt($ewp-#07e--&f((v63o-"

# CSRF e sessão não seguras (apenas para desenvolvimento)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
