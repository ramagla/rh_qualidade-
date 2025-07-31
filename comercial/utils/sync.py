from comercial.api_client import BrasmolClient
from comercial.models.clientes import Cliente
import logging
import traceback

logger = logging.getLogger(__name__)

def sync_clients():
    client = BrasmolClient()
    data = client.fetch_clients()
    registros = data if isinstance(data, list) else list(data.values())

    for obj in registros:
        cnpj = obj.get("cnpj")
        razao = obj.get("razao_social")

        if not cnpj or not razao:
            logger.warning("Ignorado (falta cnpj/razao_social): %r", obj)
            continue

        try:
            cliente = Cliente.objects.filter(cnpj=cnpj).first()

            dados_api = {
                "razao_social": razao,
                "endereco": obj.get("endereco", ""),
                "numero": obj.get("numero", "S/N"),
                "bairro": obj.get("bairro", "Não Informado"),
                "cidade": obj.get("cidade", "Não Informado"),
                "cep": obj.get("cep", "00000-000"),
                "uf": obj.get("uf", "SP"),
                "ie": obj.get("ie", ""),
                "status": "Ativo",
                "tipo_cliente": "Não Automotivo",
                "tipo_cadastro": "Cliente",
                "transportadora": None,
                "complemento": obj.get("complemento", ""),
                "telefone": obj.get("telefone", ""),
                "email": obj.get("email", ""),
                "logotipo": None,
                "coleta": False,
                "nome_contato": obj.get("nome_contato", ""),
                "email_contato": obj.get("email_contato", ""),
                "telefone_contato": obj.get("telefone_contato", ""),
                "cargo_contato": obj.get("cargo_contato", ""),
                "departamento_contato": obj.get("departamento_contato", ""),
                "icms": obj.get("icms", None),
                "cfop": obj.get("cfop", ""),
                "cond_pagamento": obj.get("condicao_pagamento", ""),
                "cod_bm": obj.get("cod_bm", ""),
                "observacao": obj.get("observacao", ""),
                "status_adimplencia": obj.get("situacao", "Adimplente"),
                "comprovante_adimplencia": None,
            }

            if cliente:
                # Verifica se há alguma diferença antes de salvar
                alterado = any(getattr(cliente, campo) != valor for campo, valor in dados_api.items())

                if alterado:
                    for campo, valor in dados_api.items():
                        setattr(cliente, campo, valor)
                    cliente.save()
                    logger.info("🔄 Cliente atualizado: %s", cnpj)
                else:
                    logger.info("✅ Cliente sem alterações: %s", cnpj)
            else:
                Cliente.objects.create(cnpj=cnpj, **dados_api)
                logger.info("➕ Cliente criado: %s", cnpj)

        except Exception as e:
            logger.error("❌ Falha ao sincronizar cliente %s (%s): %s\n%s", cnpj, razao, e, traceback.format_exc())
            continue
