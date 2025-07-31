# comercial/management/commands/sync_clientes.py

from django.core.management.base import BaseCommand
from comercial.utils.sync import sync_clients


class Command(BaseCommand):
    help = "Sincroniza os clientes com a base Brasmol via API."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔄 Iniciando sincronização de clientes..."))

        try:
            sync_clients()
            self.stdout.write(self.style.SUCCESS("✅ Sincronização concluída com sucesso."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao sincronizar clientes: {e}"))
