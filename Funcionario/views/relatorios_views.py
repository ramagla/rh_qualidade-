from django.views.generic import TemplateView
from Funcionario.models import Treinamento, Funcionario, AvaliacaoAnual,AvaliacaoTreinamento
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from datetime import date
import os
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator





def generate_training_hours_chart_styled(total_horas_por_trimestre, ano):
    # Conteúdo da função para gerar o gráfico
    plt.figure(figsize=(8, 4))
    trimestres = ['1º T', '2º T', '3º T', '4º T']
    valores = [total_horas_por_trimestre.get(t, 0) for t in range(1, 5)]
    meta = [4] * 4

    plt.bar(trimestres, valores, color='lightblue', edgecolor='green', label='Índice Mensal')
    plt.plot(trimestres, meta, color='green', marker='o', label='Meta', linewidth=2)

    plt.ylabel("Horas", fontsize=12, color='green')
    plt.ylim(0, 11)
    plt.xticks(fontsize=10, color='green')
    plt.yticks(fontsize=10, color='green')
    plt.title(f"Horas de Treinamento - {ano}", fontsize=14, color='green', weight='bold')
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png).decode('utf-8')
    plt.close()
    return graphic

@method_decorator(login_required, name='dispatch')
class RelatorioPlanilhaTreinamentosView(TemplateView):
    template_name = "relatorios/relatorio_planilha_treinamentos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_atual'] = datetime.now().strftime('%d/%m/%Y')

        # Obtendo anos disponíveis para o filtro
        anos_disponiveis = Treinamento.objects.dates('data_inicio', 'year').distinct()
        context['anos_disponiveis'] = [ano.year for ano in anos_disponiveis]

        # Pega o ano selecionado ou o ano atual
        ano = int(self.request.GET.get('ano', datetime.now().year))

        # Configuração dos trimestres
        trimestres = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}

        # Inicializar dados
        total_horas_por_mes = {mes: 0.0 for mes in range(1, 13)}
        total_horas_por_trimestre = {}
        total_horas_treinamento = 0.0

        # Processar treinamentos por mês e trimestre
        for trimestre, (mes_inicio, mes_fim) in trimestres.items():
            treinamentos = Treinamento.objects.filter(
                data_inicio__year=ano,
                data_inicio__month__gte=mes_inicio,
                data_inicio__month__lte=mes_fim
            ).order_by('data_inicio')

            # Calcula o total de horas no trimestre
            total_horas = 0.0
            for treinamento in treinamentos:
                carga_horaria = (
                    float(treinamento.carga_horaria.replace("h", "").strip())
                    if treinamento.carga_horaria else 0
                )
                participantes_count = Funcionario.objects.filter(
                    treinamentos__nome_curso=treinamento.nome_curso,
                    treinamentos__data_inicio=treinamento.data_inicio,
                    treinamentos__data_fim=treinamento.data_fim
                ).distinct().count()

                total_horas += carga_horaria * participantes_count

            # Atualizar horas totais por trimestre
            total_horas_por_trimestre[trimestre] = round(total_horas, 2)

            # Distribuir horas por mês
            for mes in range(mes_inicio, mes_fim + 1):
                total_horas_por_mes[mes] += total_horas

            total_horas_treinamento += total_horas

        # Calcular média de horas por trimestre (dividindo pelo total de funcionários ativos)
        total_funcionarios = Funcionario.objects.filter(status='Ativo').count() or 1
        media_por_funcionario = {
            trimestre: round(total / total_funcionarios, 2)
            for trimestre, total in total_horas_por_trimestre.items()
        }

        # Calculando média anual
        media_anual = sum(media_por_funcionario.values()) / len(media_por_funcionario)

        # Gerar gráfico em base64
        grafico_base64 = generate_training_hours_chart_styled(media_por_funcionario, ano)

        # Total de horas trabalhadas na empresa (base de 176 horas/mês por funcionário)
        total_horas_trabalhadas_empresa = total_funcionarios * 176 * 12  # 12 meses no ano

        # Lógica para análise de dados (se dentro da meta ou não)
        meta = 4  # Meta estabelecida
        analise_dados = {}
        for trimestre, media in media_por_funcionario.items():
            if media >= meta:
                analise_dados[trimestre] = {'status': 'Ok', 'mensagem': 'Indicador dentro da meta estabelecida'}
            else:
                analise_dados[trimestre] = {'status': 'Nok', 'mensagem': 'Indicador fora da meta estabelecida'}

        # Atualizar contexto
        context.update({
            'ano': ano,
            'trimestres': trimestres,
            'valores': media_por_funcionario,
            'media': round(media_anual, 2),
            'total_horas_por_trimestre': total_horas_por_trimestre,
            'total_horas_treinamento': total_horas_treinamento,
            'total_horas_trabalhadas_empresa': total_horas_trabalhadas_empresa,
            'grafico_base64': grafico_base64,
            'anos_disponiveis': context['anos_disponiveis'],
            'analise_dados': analise_dados,  # Adicionado para o template
        })

        return context


class RelatorioIndicadorAnualView(TemplateView):
    template_name = 'relatorios/indicador_anual.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Buscar todas as avaliações anuais
        avaliacoes = AvaliacaoAnual.objects.all()

        # Obter anos distintos
        anos = sorted(set(avaliacoes.values_list('data_avaliacao__year', flat=True)))

        # Filtrar para mostrar apenas os últimos 5 anos
        anos = anos[-5:] if len(anos) > 5 else anos

        # Calcular o índice anual por ano
        dados_por_ano = {}
        funcionarios_avaliados = {}
        total_notas = 0
        total_colaboradores = 0

        for ano in anos:
            avaliacoes_ano = avaliacoes.filter(data_avaliacao__year=ano)
            somatoria_notas = sum(
                a.calcular_classificacao()['percentual'] for a in avaliacoes_ano
            )
            total_colaboradores_ano = avaliacoes_ano.count()

            if total_colaboradores_ano > 0:
                indice = somatoria_notas / total_colaboradores_ano
                dados_por_ano[ano] = round(indice, 2)  # Arredondar para 2 casas decimais
                funcionarios_avaliados[ano] = total_colaboradores_ano

                # Acumular dados para cálculo da média geral
                total_notas += somatoria_notas
                total_colaboradores += total_colaboradores_ano
            else:
                dados_por_ano[ano] = 0  # Evitar divisão por zero
                funcionarios_avaliados[ano] = 0

        # Calcular média geral
        media = (total_notas / total_colaboradores) if total_colaboradores > 0 else 0

        # Construir análise de dados por ano
        analise_dados = {
            ano: f"({ano}) - {'Indicador dentro da Meta. Vamos manter a meta e continuar o acompanhamento.' if dados_por_ano[ano] >= 70 else 'Indicador fora da Meta. Revisar as ações corretivas.'}"
            for ano in anos
        }

        # Adicionar informações ao contexto
        context['grafico_base64'] = self.gerar_grafico(dados_por_ano)
        context['dados_por_ano'] = dados_por_ano
        context['funcionarios_avaliados'] = funcionarios_avaliados  # Adicionar números de funcionários avaliados
        context['meta'] = 70  # Meta fixa de 70%
        context['media'] = round(media, 2)  # Média geral arredondada
        context['analise_dados'] = analise_dados  # Mensagens de análise por ano

        return context


    def gerar_grafico(self, dados_por_ano):
        # Obter anos e índices
        anos = sorted(dados_por_ano.keys())
        indices = [dados_por_ano[ano] for ano in anos]
        meta = [70] * len(anos)  # Meta fixa de 70%

        # Configurar o gráfico
        plt.figure(figsize=(8, 4))
        x_pos = range(len(anos))  # Posicionamento categórico para cada ano
        plt.bar(x_pos, indices, color='lightblue', edgecolor='green', label='Índice Anual', width=0.6)
        plt.plot(x_pos, meta, color='green', marker='o', linestyle='--', linewidth=2, label='Meta')  # Linha da meta

        # Configurar o eixo X para valores categóricos (anos)
        plt.xticks(ticks=x_pos, labels=anos, fontsize=10, color='black')
        plt.yticks(range(0, 101, 10), fontsize=10, color='black')  # Escala de 0 a 100%
        plt.gca().set_facecolor('#B5E61D')  # Fundo verde

        # Configurações de título e legendas
        plt.xlabel('Ano', fontsize=12, color='green')
        plt.ylabel('Porcentagem', fontsize=12, color='black', weight='bold')
        plt.title('Índice de Avaliação Anual de Desempenho', fontsize=14, color='black', weight='bold')
        plt.ylim(0, 100)
        plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False)

        # Geração do gráfico em base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        return base64.b64encode(image_png).decode('utf-8')

@login_required
def cronograma_treinamentos(request):
    # Obtém os filtros
    ano = request.GET.get('ano', None)
    departamento = request.GET.get('departamento', None)

    # Define o ano padrão como o ano atual, se necessário
    ano = int(ano) if ano else datetime.now().year

    # Filtra os treinamentos
    treinamentos = Treinamento.objects.filter(data_inicio__year=ano)
    if departamento:
        treinamentos = treinamentos.filter(funcionarios__local_trabalho=departamento)

    # Obter anos disponíveis para o filtro
    anos_disponiveis = Treinamento.objects.dates('data_inicio', 'year', order='DESC')
    anos_disponiveis = [data.year for data in anos_disponiveis]

    # Obter departamentos únicos
    departamentos = Funcionario.objects.values_list('local_trabalho', flat=True).distinct()

    # Gerar os meses dinamicamente com base no ano filtrado
    meses = [datetime(ano, mes, 1).strftime("%b/%y").capitalize() for mes in range(1, 13)]

    # Monta o contexto para o template
    context = {
        'treinamentos': treinamentos,
        'anos_disponiveis': anos_disponiveis,
        'departamentos': departamentos,
        'ano': ano,
        'filtro_departamento': departamento,
        'data_atual': datetime.now().strftime('%d/%m/%Y'),
        'meses': meses,
    }

    return render(request, 'relatorios/cronograma_treinamentos.html', context)

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from Funcionario.models import AvaliacaoTreinamento, Funcionario

@login_required
def cronograma_avaliacao_eficacia(request):
    # Obtém os filtros da URL
    ano = request.GET.get('ano', None)
    departamento = request.GET.get('departamento', None)

    # Define o ano padrão como o ano atual, se necessário
    ano = int(ano) if ano else datetime.now().year

    # Filtra as avaliações
    avaliacoes = AvaliacaoTreinamento.objects.filter(data_avaliacao__year=ano)
    if departamento:
        avaliacoes = avaliacoes.filter(funcionario__local_trabalho=departamento)

    # Obter anos disponíveis para o filtro
    anos_disponiveis = AvaliacaoTreinamento.objects.dates('data_avaliacao', 'year', order='DESC')
    anos_disponiveis = [data.year for data in anos_disponiveis]

    # Obter departamentos únicos
    departamentos = Funcionario.objects.values_list('local_trabalho', flat=True).distinct()

    # Gerar os meses dinamicamente com base no ano filtrado
    meses = [datetime(ano, mes, 1).strftime("%b/%y").capitalize() for mes in range(1, 13)]

    # Processar avaliações para definir o mês correto no cronograma
    avaliacoes_processadas = []
    for avaliacao in avaliacoes:
        if avaliacao.data_avaliacao and avaliacao.periodo_avaliacao:
            data_final = avaliacao.data_avaliacao + timedelta(days=avaliacao.periodo_avaliacao)
            mes_final = data_final.strftime("%b/%y").capitalize()
        else:
            data_final = None
            mes_final = None  # Caso não tenha data

        # Adiciona a propriedade mes_final para cada avaliação
        avaliacoes_processadas.append({
            'avaliacao': avaliacao,
            'data_final': data_final,  # Adiciona para uso direto no template
            'mes_final': mes_final,
            'periodo_avaliacao': avaliacao.periodo_avaliacao,  # Inclui para evitar erro
        })

    # Monta o contexto para o template
    context = {
        'avaliacoes': avaliacoes_processadas,
        'anos_disponiveis': anos_disponiveis,
        'departamentos': departamentos,
        'ano': ano,
        'filtro_departamento': departamento,
        'data_atual': datetime.now().strftime('%d/%m/%Y'),
        'meses': meses,
    }

    return render(request, 'relatorios/cronograma_avaliacao_eficacia.html', context)
