from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.shortcuts import render

from metrologia.models.models_dispositivos import Dispositivo

from ..models.models_calibracao import Calibracao
from ..models.models_tabelatecnica import TabelaTecnica


def cronograma_equipamentos(request):
    # Filtros
    today = date.today()
    ano = request.GET.get("ano")
    grandeza = request.GET.get("grandeza")
    tipo_avaliacao = request.GET.get("tipo_avaliacao")

    # Base de consulta com anotação para próxima calibração
    equipamentos = TabelaTecnica.objects.filter(status__iexact="Ativo").order_by(
        "codigo"
    )

    # Aplicar filtros
    if ano:
        equipamentos = equipamentos.filter(data_ultima_calibracao__year=ano)
    if grandeza:
        equipamentos = equipamentos.filter(unidade_medida=grandeza)
    if tipo_avaliacao:
        equipamentos = equipamentos.filter(tipo_avaliacao=tipo_avaliacao)

    # Lista para armazenar dados formatados
    equipamento_data = []

    for equipamento in equipamentos:
        # Dados de calibração relacionados
        calibracao = Calibracao.objects.filter(codigo=equipamento).last()

        # Calcular próxima calibração
        proxima_calibracao = (
            equipamento.data_ultima_calibracao
            + timedelta(days=equipamento.frequencia_calibracao * 30)
            if equipamento.data_ultima_calibracao and equipamento.frequencia_calibracao
            else None
        )

        # Formatar a capacidade com valores seguros
        capacidade_minima = (
            f"{equipamento.capacidade_minima:.4f}"
            if equipamento.capacidade_minima
            else "0.0000"
        )
        capacidade_maxima = (
            f"{equipamento.capacidade_maxima:.4f}"
            if equipamento.capacidade_maxima
            else "0.0000"
        )
        unidade_medida = (
            equipamento.unidade_medida if equipamento.unidade_medida else ""
        )
        capacidade = (
            f"{capacidade_minima} - {capacidade_maxima} {unidade_medida}".strip()
        )

        equipamento_data.append(
            {
                "codigo": equipamento.codigo,
                "nome_equipamento": equipamento.nome_equipamento,
                "fabricante": equipamento.fabricante,
                "capacidade": capacidade,
                "resolucao": (
                    f"{equipamento.resolucao} {equipamento.unidade_medida}"
                    if equipamento.unidade_medida
                    else "N/A"
                ),
                "responsavel": (
                    equipamento.responsavel.nome.split()[0]
                    if equipamento.responsavel
                    else "N/A"
                ),
                "data_ultima_calibracao": equipamento.data_ultima_calibracao,  # Sem strftime
                "data_proxima_calibracao": proxima_calibracao,  # Sem strftime
                "frequencia_calibracao": equipamento.frequencia_calibracao or "-",
                "laboratorio": calibracao.laboratorio if calibracao else "N/A",
                "numero_certificado": (
                    calibracao.numero_certificado if calibracao else "N/A"
                ),
                "erro_equipamento": (
                    calibracao.erro_equipamento if calibracao else "N/A"
                ),
                "incerteza": calibracao.incerteza if calibracao else "N/A",
                "l": calibracao.l if calibracao else "N/A",
                "exatidao_requerida": (
                    equipamento.exatidao_requerida
                    if equipamento.exatidao_requerida
                    else "N/A"
                ),
                "status": calibracao.status if calibracao else "N/A",
            }
        )

    # Filtros dinâmicos
    anos_disponiveis = TabelaTecnica.objects.dates(
        "data_ultima_calibracao", "year"
    ).distinct()
    tipos_grandeza = TabelaTecnica.objects.values_list(
        "unidade_medida", flat=True
    ).distinct()
    tipos_avaliacao = TabelaTecnica.objects.values_list(
        "tipo_avaliacao", flat=True
    ).distinct()

    context = {
        "equipamentos": equipamento_data,
        "anos_disponiveis": [ano.year for ano in anos_disponiveis],
        "tipos_grandeza": tipos_grandeza,
        "tipos_avaliacao": tipos_avaliacao,
        "ano": ano,
        "grandeza": grandeza,
        "tipo_avaliacao": tipo_avaliacao,
        "today": today,
    }

    return render(request, "cronogramas/cronograma_equipamentos.html", context)


def cronograma_dispositivos(request):
    today = date.today()

    # Filtros
    ano = request.GET.get("ano")
    cliente = request.GET.get("cliente")

    # Base de consulta
    dispositivos = Dispositivo.objects.all()

    if ano:
        dispositivos = dispositivos.filter(data_ultima_calibracao__year=ano)
    if cliente:
        dispositivos = dispositivos.filter(cliente__iexact=cliente)

    dispositivo_data = []
    for dispositivo in dispositivos:
        # Obter a movimentação mais recente do tipo "saida"
        ultima_saida = (
            dispositivo.controle_entrada_saida.filter(tipo_movimentacao="saida")
            .order_by("-data_movimentacao")
            .first()
        )

        # Obter a movimentação mais recente (independente do tipo) para o retorno, setor, etc.
        ultima_movimentacao = dispositivo.controle_entrada_saida.order_by(
            "-data_movimentacao"
        ).first()

        # Definir valores padrão para evitar erros quando não houver movimentações
        data_ultima_saida = ultima_saida.data_movimentacao if ultima_saida else None
        data_retorno = (
            ultima_movimentacao.data_movimentacao if ultima_movimentacao else None
        )
        situacao = ultima_movimentacao.situacao if ultima_movimentacao else ""
        observacao = ultima_movimentacao.observacao if ultima_movimentacao else ""

        # Calcular próxima calibração
        proxima_calibracao = (
            dispositivo.data_ultima_calibracao
            + relativedelta(months=dispositivo.frequencia_calibracao)
            if dispositivo.data_ultima_calibracao and dispositivo.frequencia_calibracao
            else None
        )

        dispositivo_data.append(
            {
                "codigo": dispositivo.codigo,
                "qtde": dispositivo.qtde,
                "cliente": dispositivo.cliente,
                "descricao": dispositivo.descricao,
                "estudo_realizado": dispositivo.estudo_realizado,
                "data_ultima_calibracao": dispositivo.data_ultima_calibracao,  # Incluído
                "data_proxima_calibracao": proxima_calibracao,
                "local_armazenagem": dispositivo.local_armazenagem,
                "data_ultima_saida": data_ultima_saida,
                "data_retorno": data_retorno,
                "setor": ultima_saida.setor if ultima_saida else "",
                "situacao": situacao,
                "observacoes": observacao,
            }
        )

    # Filtros dinâmicos
    anos_disponiveis = Dispositivo.objects.dates(
        "data_ultima_calibracao", "year"
    ).distinct()
    clientes_disponiveis = Dispositivo.objects.values_list(
        "cliente", flat=True
    ).distinct()

    context = {
        "dispositivos": dispositivo_data,
        "anos_disponiveis": [ano.year for ano in anos_disponiveis],
        "clientes_disponiveis": clientes_disponiveis,
        "ano": ano,
        "cliente": cliente,
        "today": today,
    }

    return render(request, "cronogramas/cronograma_dispositivos.html", context)
