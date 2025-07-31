from django.core.management.base import BaseCommand
from comercial.utils.sync import sync_clients, sync_products

class Command(BaseCommand):
    help = "Sincroniza clientes e produtos da API Brasmol via API Key"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Sincronizando clientes...")
        sync_clients()
        self.stdout.write("✅ Clientes sincronizados")

        self.stdout.write("🔄 Sincronizando produtos...")
        sync_products()
        self.stdout.write("✅ Produtos sincronizados")
