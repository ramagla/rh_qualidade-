# Definir a versão do Python
ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependências do psycopg2 e WeasyPrint
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    gobject-introspection \
    libgirepository1.0-dev \
    libgdk-pixbuf2.0-0 \
    gir1.2-pango-1.0 \
    && rm -rf /var/lib/apt/lists/*

# Criar e definir o diretório de trabalho
RUN mkdir -p /code
WORKDIR /code

# Copiar e instalar dependências
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

# Copiar o código do projeto
COPY . /code

# Expor a porta de serviço
EXPOSE 8000

# Comando para iniciar o Gunicorn
CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "rh_qualidade.wsgi"]
