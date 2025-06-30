import os
import sys

# Forçar o uso de backports.zoneinfo para Python < 3.9
if sys.version_info < (3, 9):
    import backports.zoneinfo as zoneinfo
else:
    import zoneinfo

from celery import Celery

# Configuração do Django para o Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rh_qualidade.settings")

app = Celery("rh_qualidade")

# Lê configurações do Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descobre automaticamente tarefas registradas nos apps
app.autodiscover_tasks()

# Configurações adicionais do Celery
app.conf.update(
    task_always_eager=False,  # As tarefas não são executadas de forma síncrona
    worker_hijack_root_logger=False,  # Evita substituição de logs globais
)

app.conf.beat_schedule = {
    "test_task": {
        "task": "alerts.tasks.enviar_alertas_calibracao",
        "schedule": 60.0,  # Executar a cada 60 segundos
    },
     "alertas_proximos_fornecedores": {
        "task": "qualidade_fornecimento.tasks.enviar_alertas_fornecedores_proximos",
        "schedule": 86400.0,  # Executar a cada 24 horas
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
