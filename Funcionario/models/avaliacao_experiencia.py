from datetime import timedelta

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario


class AvaliacaoExperiencia(models.Model):
    """
    Representa a avaliação de experiência de um funcionário recém-contratado,
    contendo critérios como adaptação, interesse e orientação final.
    """

    data_avaliacao = models.DateField(
        verbose_name="Data da Avaliação"
    )
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    gerencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Gerência"
    )

    adaptacao_trabalho = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Adaptação ao Trabalho"
    )
    interesse = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Interesse"
    )
    relacionamento_social = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Relacionamento Social"
    )
    capacidade_aprendizagem = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Capacidade de Aprendizagem"
    )
    anexo = models.FileField(
        upload_to='avaliacoes/experiencia/',
        blank=True,
        null=True,
        verbose_name="Anexo"
    )

    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    orientacao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Orientação"
    )

    @property
    def get_status_avaliacao(self):
        """
        Retorna o status da avaliação com emoji com base na orientação final.
        """
        if self.orientacao == "Efetivar":
            return "😃 Efetivar"
        elif self.orientacao == "Encaminhar p/ Treinamento":
            return "😊 Treinamento"
        elif self.orientacao == "Desligar":
            return "😕 Desligar"
        return "Indeterminado"

    def get_status_prazo(self):
        """
        Verifica se a avaliação está dentro do prazo de 30 dias.
        """
        hoje = timezone.now().date()
        data_limite = self.data_avaliacao + timedelta(days=30)
        return "Dentro do Prazo" if data_limite >= hoje else "Em Atraso"

    def __str__(self):
        return f"Avaliação de Experiência de {self.funcionario} em {self.data_avaliacao.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name_plural = "Avaliações de Experiência"
