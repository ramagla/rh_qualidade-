import os
from datetime import date, datetime

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from qualidade_fornecimento.forms.relatorio_avaliacao_form import RelatorioAvaliacaoForm
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.utils import gerar_grafico_velocimetro


def calcular_intervalo(semestre, ano):
    if semestre == "1":
        inicio = date(ano, 1, 1)
        fim = date(ano, 6, 30)
    else:
        inicio = date(ano, 7, 1)
        fim = date(ano, 12, 31)
    return inicio, fim


def relatorio_avaliacao_view(request):
    ano_atual = datetime.today().year
    semestre_atual = "1" if datetime.today().month <= 6 else "2"

    if request.method == "POST":
        form = RelatorioAvaliacaoForm(request.POST)
        if form.is_valid():
            ano = form.cleaned_data["ano"]
            semestre = form.cleaned_data["semestre"]
            fornecedor = form.cleaned_data["fornecedor"]
            tipo = form.cleaned_data["tipo"]
            inicio, fim = calcular_intervalo(semestre, ano)

            if tipo == "servico":
                dados = InspecaoServicoExterno.objects.filter(
                    servico__fornecedor=fornecedor,
                    servico__data_envio__range=[inicio, fim],
                )
                reprovados = sum(
                    1
                    for d in dados
                    if d.status_geral() in ["Reprovado", "Aprovado Condicionalmente"]
                )
                atrasos = [
                    s.servico.atraso_em_dias
                    for s in dados
                    if hasattr(s.servico, "atraso_em_dias")
                    and s.servico.atraso_em_dias is not None
                ]
            else:
                dados = RelacaoMateriaPrima.objects.filter(
                    fornecedor=fornecedor, data_entrada__range=[inicio, fim]
                )
                reprovados = dados.filter(
                    status__in=["Reprovado", "Aprovado Condicionalmente"]
                ).count()
                atrasos = [
                    d.atraso_em_dias for d in dados if d.atraso_em_dias is not None
                ]

            total = max(1, dados.count())
            iqf = 1 - (reprovados / total)
            ip = 1 - (sum(atrasos) / len(atrasos) / 100) if atrasos else 1
            pontuacao = (fornecedor.score or 0) / 100  # transformar score em fração

            # Ponderações
            iqf_pond = iqf * 0.5
            ip_pond = ip * 0.3
            iqs = pontuacao * 0.2
            iqg = round(iqf_pond + ip_pond + iqs, 4)

            # Classificação
            if iqg >= 0.75:
                classificacao = "A - Qualificado"
                mensagem = "Gostaríamos de parabenizá-los pelo atingimento das metas e enfatizamos a importância de manter o alto nível de desempenho nas próximas avaliações."
            elif iqg <= 0.49:
                classificacao = "C - Não Qualificado"
                mensagem = "O desempenho nesta avaliação não atingiu os critérios mínimos. O fornecedor será submetido à apreciação da Diretoria, e deverá apresentar um plano de ação para continuidade da parceria."
            else:
                classificacao = "B - Qualificado Condicionalmente"
                mensagem = "Identificamos um desempenho próximo ao esperado. Solicitamos a apresentação de um plano de ação visando a correção dos desvios observados."

            # 🔧 Caminho do gráfico
            nome_arquivo = f"iqg_{fornecedor.id}_{ano}_{semestre}.png"
            caminho_absoluto = os.path.join(
                settings.MEDIA_ROOT, "graficos", nome_arquivo
            )
            caminho_relativo = os.path.join(
                settings.MEDIA_URL, "graficos", nome_arquivo
            )

            os.makedirs(os.path.dirname(caminho_absoluto), exist_ok=True)
            imagem_grafico = gerar_grafico_velocimetro(iqg * 100)

            contexto = {
                "titulo": f"DESEMPENHO - {semestre}º SEMESTRE DE {ano}",
                "fornecedor": fornecedor,
                "contato": fornecedor.especialista_nome or "Não informado",
                "iqf": iqf * 100,
                "ip": ip * 100,
                "pontuacao": fornecedor.score or 0,
                "iqf_pond": iqf_pond * 100,
                "ip_pond": ip_pond * 100,
                "iqs": iqs * 100,
                "iqg": iqg * 100,
                "classificacao": classificacao.split(" ")[0],
                "mensagem": mensagem,
                "form": form,
                "exibir": True,
                "grafico_base64": imagem_grafico,
            }
            return render(request, "relatorios/relatorio_avaliacao.html", contexto)

    else:
        form = RelatorioAvaliacaoForm(
            initial={"ano": ano_atual, "semestre": semestre_atual}
        )

    return render(
        request, "relatorios/relatorio_avaliacao.html", {"form": form, "exibir": False}
    )
