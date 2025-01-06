from datetime import timedelta,date
from django.shortcuts import render
from ..models.models_tabelatecnica import TabelaTecnica
from ..models.models_calibracao import Calibracao

def cronograma_equipamentos(request):
    # Filtros
    today = date.today()
    ano = request.GET.get('ano')
    grandeza = request.GET.get('grandeza')
    tipo_avaliacao = request.GET.get('tipo_avaliacao')

    # Base de consulta com anotação para próxima calibração
    equipamentos = TabelaTecnica.objects.filter(status__iexact='Ativo').order_by('codigo')


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
            equipamento.data_ultima_calibracao + timedelta(days=equipamento.frequencia_calibracao * 30)
            if equipamento.data_ultima_calibracao and equipamento.frequencia_calibracao
            else None
        )


        # Formatar a capacidade com valores seguros
        capacidade_minima = f"{equipamento.capacidade_minima:.4f}" if equipamento.capacidade_minima else "0.0000"
        capacidade_maxima = f"{equipamento.capacidade_maxima:.4f}" if equipamento.capacidade_maxima else "0.0000"
        unidade_medida = equipamento.unidade_medida if equipamento.unidade_medida else ""
        capacidade = f"{capacidade_minima} - {capacidade_maxima} {unidade_medida}".strip()

        equipamento_data.append({
            "codigo": equipamento.codigo,
            "nome_equipamento": equipamento.nome_equipamento,
            "fabricante": equipamento.fabricante,
            "capacidade": capacidade,
            "resolucao": f"{equipamento.resolucao} {equipamento.unidade_medida}" if equipamento.unidade_medida else "N/A",
            "responsavel": equipamento.responsavel.nome.split()[0] if equipamento.responsavel else "N/A",
            "data_ultima_calibracao": equipamento.data_ultima_calibracao,  # Sem strftime
            "data_proxima_calibracao": proxima_calibracao,  # Sem strftime
            "frequencia_calibracao": equipamento.frequencia_calibracao or "-",
            "laboratorio": calibracao.laboratorio if calibracao else "N/A",
            "numero_certificado": calibracao.numero_certificado if calibracao else "N/A",
            "erro_equipamento": calibracao.erro_equipamento if calibracao else "N/A",
            "incerteza": calibracao.incerteza if calibracao else "N/A",
            "l": calibracao.l if calibracao else "N/A",
            "exatidao_requerida": equipamento.exatidao_requerida if equipamento.exatidao_requerida else "N/A",
            "status": calibracao.status if calibracao else "N/A",
        })

    # Filtros dinâmicos
    anos_disponiveis = TabelaTecnica.objects.dates('data_ultima_calibracao', 'year').distinct()
    tipos_grandeza = TabelaTecnica.objects.values_list('unidade_medida', flat=True).distinct()
    tipos_avaliacao = TabelaTecnica.objects.values_list('tipo_avaliacao', flat=True).distinct()

    context = {
        'equipamentos': equipamento_data,
        'anos_disponiveis': [ano.year for ano in anos_disponiveis],
        'tipos_grandeza': tipos_grandeza,
        'tipos_avaliacao': tipos_avaliacao,
        'ano': ano,
        'grandeza': grandeza,
        'tipo_avaliacao': tipo_avaliacao,
        'today': today, 
    }

    return render(request, 'cronogramas/cronograma_equipamentos.html', context)





def cronograma_dispositivos(request):
    return render(request, 'metrologia/cronograma_dispositivos.html')
