from django.db import models
from .funcionario import Funcionario


class AvaliacaoAnual(models.Model):
    """
    Representa uma avaliação anual realizada para um funcionário com base em critérios de desempenho.
    """

    data_avaliacao = models.DateField(verbose_name="Data da Avaliação")
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    centro_custo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Centro de Custo"
    )

    # Campos do questionário
    postura_seg_trabalho = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Postura em Segurança do Trabalho"
    )
    qualidade_produtividade = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Qualidade e Produtividade"
    )
    trabalho_em_equipe = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Trabalho em Equipe"
    )
    comprometimento = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Comprometimento"
    )
    disponibilidade_para_mudancas = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Disponibilidade para Mudanças"
    )
    disciplina = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Disciplina"
    )
    rendimento_sob_pressao = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Rendimento sob Pressão"
    )
    proatividade = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Proatividade"
    )
    comunicacao = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Comunicação"
    )
    assiduidade = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Assiduidade"
    )
    avaliacao_global_avaliador = models.TextField(
        blank=True,
        null=True,
        verbose_name="Avaliação Global do Avaliador"
    )
    avaliacao_global_avaliado = models.TextField(
        blank=True,
        null=True,
        verbose_name="Autoavaliação do Avaliado"
    )
    anexo = models.FileField(
        upload_to='avaliacoes/anual/',
        blank=True,
        null=True,
        verbose_name="Anexo"
    )

    # Lista dos campos numéricos avaliados
    CAMPOS_AVALIADOS = [
        "postura_seg_trabalho",
        "qualidade_produtividade",
        "trabalho_em_equipe",
        "comprometimento",
        "disponibilidade_para_mudancas",
        "disciplina",
        "rendimento_sob_pressao",
        "proatividade",
        "comunicacao",
        "assiduidade",
    ]

    def calcular_classificacao(self):
        """
        Calcula o percentual de desempenho com base nos campos avaliativos e
        retorna a classificação correspondente.
        """
        total_pontos = sum(
            getattr(self, campo) or 0 for campo in self.CAMPOS_AVALIADOS
        )

        if total_pontos == 0:
            return {"percentual": 0, "status": "Indeterminado"}

        percentual = (total_pontos / 40) * 100
        status = ""

        if 25 <= percentual <= 45:
            status = "Ruim"
        elif 46 <= percentual <= 65:
            status = "Regular"
        elif 66 <= percentual <= 84:
            status = "Bom"
        elif 85 <= percentual <= 100:
            status = "Ótimo"

        return {"percentual": percentual, "status": status}

    @staticmethod
    def get_status_text(value):
        """
        Retorna o texto correspondente ao valor numérico da nota.
        """
        status_map = {1: "Ruim", 2: "Regular", 3: "Bom", 4: "Ótimo"}
        return status_map.get(value, "Indeterminado")

    def __str__(self):
        return f"Avaliação de {self.funcionario.nome} em {self.data_avaliacao.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name_plural = "Avaliações Anuais"
