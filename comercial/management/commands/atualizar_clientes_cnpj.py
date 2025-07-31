import requests
from django.core.management.base import BaseCommand
from comercial.models import Cliente


class Command(BaseCommand):
    help = "Atualiza dados dos clientes com base no CNPJ via BrasilAPI (somente se houver alterações)"

    def handle(self, *args, **options):
        atualizados = 0
        erros = 0
        ignorados = 0

        clientes = Cliente.objects.filter(cnpj__isnull=False).exclude(cnpj="")

        for cliente in clientes:
            cnpj = cliente.cnpj.replace(".", "").replace("/", "").replace("-", "").strip()

            if len(cnpj) != 14:
                self.stdout.write(f"❌ CNPJ inválido para {cliente.razao_social}: {cnpj}")
                erros += 1
                continue

            try:
                response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}")
                response.raise_for_status()
                data = response.json()

                # Construir os dados recebidos
                dados_api = {
                    "razao_social": data.get("razao_social", cliente.razao_social),
                    "endereco": f"{data.get('descricao_tipo_de_logradouro', '')} {data.get('logradouro', '')}".strip(),
                    "numero": data.get("numero") or cliente.numero,
                    "complemento": data.get("complemento") or cliente.complemento,
                    "bairro": data.get("bairro") or cliente.bairro,
                    "cidade": data.get("municipio") or cliente.cidade,
                    "cep": data.get("cep") or cliente.cep,
                    "uf": data.get("uf") or cliente.uf,
                    "ie": data.get("inscricoes_estaduais", [{}])[0].get("numero") if data.get("inscricoes_estaduais") else cliente.ie
                }

                # Verificar se houve alguma alteração
                alterado = any(getattr(cliente, campo) != valor for campo, valor in dados_api.items())

                if alterado:
                    for campo, valor in dados_api.items():
                        setattr(cliente, campo, valor)
                    cliente.save()
                    self.stdout.write(f"🔄 Atualizado: {cliente.razao_social}")
                    atualizados += 1
                else:
                    self.stdout.write(f"✅ Sem alterações: {cliente.razao_social}")
                    ignorados += 1

            except Exception as e:
                self.stdout.write(f"❌ Erro ao atualizar {cliente.razao_social} ({cnpj}): {e}")
                erros += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ {atualizados} cliente(s) atualizados com sucesso."))
        self.stdout.write(self.style.WARNING(f"⚠️ {ignorados} cliente(s) sem alteração."))
        self.stdout.write(self.style.ERROR(f"❌ {erros} cliente(s) com erro durante atualização."))
