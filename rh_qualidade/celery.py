import os
from celery import Celery

# Configuração do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rh_qualidade.settings')

app = Celery('rh_qualidade')

# Lê configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre automaticamente tarefas registradas nos apps
app.autodiscover_tasks()

# Configurações adicionais do Celery
app.conf.update(
    task_always_eager=False,  # As tarefas não são executadas de forma síncrona
    worker_hijack_root_logger=False,  # Evita substituição de logs globais
)

app.conf.beat_schedule = {}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
