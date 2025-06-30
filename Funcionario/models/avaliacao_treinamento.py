from datetime import timedelta

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario
from .treinamento import Treinamento


class AvaliacaoTreinamento(models.Model):
    OPCOES_CONHECIMENTO = [
        (1, "Não possui conhecimento mínimo da metodologia para sua aplicação."),
        (2, "Apresenta deficiências nos conceitos, o que compromete a aplicação."),
        (
            3,
            "Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.",
        ),
        (4, "Possui domínio necessário da metodologia e a utiliza adequadamente."),
        (5, "Possui completo domínio e utiliza a metodologia com excelência."),
    ]

    OPCOES_APLICACAO = [
        (1, "Está muito abaixo do esperado."),
        (2, "Aplicação está abaixo do esperado."),
        (3, "Aplicação é razoável, mas não dentro do esperado."),
        (4, "Aplicação está adequada e corresponde às expectativas."),
        (5, "Aplicação excede as expectativas."),
    ]

    OPCOES_RESULTADOS = [
        (1, "Nenhum resultado foi obtido efetivamente até o momento."),
        (2, "As melhorias obtidas estão muito abaixo do esperado."),
        (3, "As melhorias obtidas são consideráveis, mas não dentro do esperado."),
        (4, "As melhorias obtidas são boas e estão dentro do esperado."),
        (5, "As melhorias obtidas excederam as expectativas."),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    treinamento = models.ForeignKey(
        Treinamento, on_delete=models.CASCADE, related_name="avaliacoes"
    )

    data_avaliacao = models.DateField()
    periodo_avaliacao = models.IntegerField(default=60)  # Período de avaliação em dias
    anexo = models.FileField(
        upload_to="avaliacoes_treinamento/",
        null=True,
        blank=True,
        verbose_name="Comprovante/Anexo",
    )


    def get_status_prazo(self):
        # Calcula a data limite adicionando o período ao dia da avaliação
        data_limite = self.data_avaliacao + timedelta(days=self.periodo_avaliacao)

        # Compara a data atual com a data limite
        if timezone.now().date() <= data_limite:
            return "Dentro do Prazo"
        return "Em Atraso"

    responsavel_1 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_1",
    )
    responsavel_2 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_2",
    )
    responsavel_3 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_3",
    )

    pergunta_1 = models.IntegerField(choices=OPCOES_CONHECIMENTO, null=True, blank=True)
    pergunta_2 = models.IntegerField(choices=OPCOES_APLICACAO, null=True, blank=True)
    pergunta_3 = models.IntegerField(choices=OPCOES_RESULTADOS, null=True, blank=True)

    descricao_melhorias = models.TextField(default="Nenhuma melhoria descrita", blank=True)
    avaliacao_geral = models.IntegerField(
        choices=[
            (1, "Pouco eficaz"),
            (2, "Eficaz"),
            (3, "Razoável"),
            (4, "Bom"),
            (5, "Muito eficaz"),
        ],
        null=True,
        blank=True
    )
