# Bibliotecas padrão
from datetime import date

# Django
from django.shortcuts import get_object_or_404
from django.db.models import CharField, Case, Value, When


# App Interno
from Funcionario.models import AvaliacaoTreinamento
from Funcionario.models import Funcionario, IntegracaoFuncionario, Treinamento

def criar_ou_atualizar_avaliacao(treinamento):
    """
    Cria ou atualiza avaliações para os participantes de um treinamento.
    """
    if treinamento.necessita_avaliacao and treinamento.status == "concluido":
        for participante in treinamento.funcionarios.all():
            avaliacao, criada = AvaliacaoTreinamento.objects.get_or_create(
                funcionario=participante,
                treinamento=treinamento,
                defaults={
                    "data_avaliacao": treinamento.data_fim or date.today(),
                    "periodo_avaliacao": 60,
                    "pergunta_1": None,
                    "pergunta_2": None,
                    "pergunta_3": None,
                    "responsavel_1": participante.responsavel,
                    "descricao_melhorias": "Aguardando avaliação",
                    "avaliacao_geral": None,
                }
            )
            if not criada:
                avaliacao.data_avaliacao = treinamento.data_fim or date.today()
                avaliacao.pergunta_1 = None
                avaliacao.pergunta_2 = None
                avaliacao.pergunta_3 = None
                avaliacao.responsavel_1 = participante.responsavel
                avaliacao.descricao_melhorias = "Aguardando avaliação"
                avaliacao.avaliacao_geral = None
                avaliacao.save()


def obter_treinamentos_requeridos(filtro_departamento, filtro_data_inicio, filtro_data_fim):
    """
    Retorna treinamentos requeridos aplicando filtros de departamento e data.
    """
    funcionarios = Funcionario.objects.all()
    if filtro_departamento:
        funcionarios = funcionarios.filter(local_trabalho=filtro_departamento)

    treinamentos = Treinamento.objects.filter(
        funcionarios__in=funcionarios,
        status="requerido"
    )

    if filtro_data_inicio:
        treinamentos = treinamentos.filter(data_inicio__gte=filtro_data_inicio)
    if filtro_data_fim:
        treinamentos = treinamentos.filter(data_fim__lte=filtro_data_fim)

    treinamentos = treinamentos.annotate(
        situacao_treinamento=Case(
            When(status="aprovado", then=Value("APROVADO")),
            When(status="reprovado", then=Value("REPROVADO")),
            default=Value("PENDENTE"),
            output_field=CharField(),
        )
    ).order_by("funcionarios__nome")

    chefia_imediata = funcionarios.first().responsavel if funcionarios.exists() else None

    return treinamentos, chefia_imediata


def obter_dados_relatorio_f003(funcionario_id):
    """
    Busca dados de treinamento e integração de um funcionário para o relatório F003.
    """
    funcionario = Funcionario.objects.get(id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionarios=funcionario)
    integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).first()

    return funcionario, treinamentos, integracao
