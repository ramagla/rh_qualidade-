import calendar
import os
from calendar import monthrange

from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from .funcionario import Funcionario


class Treinamento(models.Model):
    TIPO_TREINAMENTO_CHOICES = [
        ("interno", "Interno"),
        ("externo", "Externo"),
    ]

    CATEGORIA_CHOICES = [
        ("capacitacao", "Capacitação"),
        ("tecnico", "Técnico"),
        ("graduacao", "Graduação"),
        ("pos-graduacao", "Pos-graduação"),
        ("treinamento", "Treinamento"),
        ("divulgacao", "Divulgação"),
    ]

    STATUS_CHOICES = [
        ("planejado", "Planejado"), 
        ("concluido", "Concluído"),
        ("trancado", "Trancado"),
        ("cursando", "Cursando"),
        ("requerido", "Requerido"),
    ]

    SITUACAO_CHOICES = [
        ("aprovado", "Aprovado"),
        ("reprovado", "Reprovado"),
    ]

    PLANEJADO_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
    ]

    funcionarios = models.ManyToManyField(Funcionario, related_name="treinamentos")
    tipo = models.CharField(max_length=50, choices=TIPO_TREINAMENTO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    nome_curso = models.CharField(max_length=100)
    instituicao_ensino = models.CharField(max_length=255, default="Bras-Mol")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="cursando")
    data_inicio = models.DateField()
    data_fim = models.DateField()
    carga_horaria = models.CharField(max_length=50)
    anexo = models.FileField(upload_to="certificados/", blank=True, null=True)
    descricao = CKEditor5Field(config_name="default", blank=True, null=True)
    situacao = models.CharField(
        max_length=50,
        choices=SITUACAO_CHOICES,
        blank=True,
        null=True,
        help_text="Campo exibido apenas para treinamentos requeridos.",
    )
    planejado = models.CharField(
        max_length=3, choices=PLANEJADO_CHOICES, default="nao", verbose_name="Planejado"
    )
    necessita_avaliacao = models.BooleanField(default=False)


    def __str__(self):
        return self.nome_curso

    def save(self, *args, **kwargs):
        if self.status != "requerido":
            self.situacao = None  # Remove valor caso status não seja 'requerido'

        # Salva o treinamento antes de associar os funcionários
        super().save(*args, **kwargs)

        # Atualiza a escolaridade dos funcionários associados, se os critérios forem atendidos
        if self.status == "concluido" and self.categoria in [
            "tecnico",
            "graduacao",
            "pos-graduacao",
            "mestrado",
            "doutorado",
        ]:
            for funcionario in self.funcionarios.all():
                funcionario.atualizar_escolaridade()

    def delete(self, *args, **kwargs):
        if self.anexo:
            if os.path.isfile(self.anexo.path):
                os.remove(self.anexo.path)
        super().delete(*args, **kwargs)

    @property
    def meses_agendados(self):
        if not self.data_inicio or not self.data_fim:
            return []

        # Lista para armazenar os meses
        meses = []
        ano_inicio, mes_inicio = self.data_inicio.year, self.data_inicio.month
        ano_fim, mes_fim = self.data_fim.year, self.data_fim.month

        # Percorre o intervalo de anos e meses
        for ano in range(ano_inicio, ano_fim + 1):
            mes_inicial = mes_inicio if ano == ano_inicio else 1
            mes_final = mes_fim if ano == ano_fim else 12

            for mes in range(mes_inicial, mes_final + 1):
                # Formata como "Jan/24", "Fev/24", etc.
                meses.append(f"{calendar.month_abbr[mes].capitalize()}/{str(ano)[-2:]}")

        return meses
