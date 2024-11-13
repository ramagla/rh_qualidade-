from .base import *
import dj_database_url

# Desativar modo de depuração em produção
DEBUG = False
ALLOWED_HOSTS = ['sua-url-de-producao.com', 'rh-qualidade.fly.dev']

# Configuração de banco de dados para produção usando dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'postgres://usuario:senha@localhost:5432/nome_do_banco')
    )
}

# Chave secreta para produção a partir de uma variável de ambiente
SECRET_KEY = os.getenv('SECRET_KEY')

# Configurações de segurança
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://rh-qualidade.fly.dev']
