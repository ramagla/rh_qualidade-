from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils.timezone import now

from Funcionario.models import Funcionario


class TabelaTecnica(models.Model):
    UNIDADE_MEDIDA_CHOICES = [
        ("mm", "Milímetros"),
        ("kg.cm", "Kilograma-centímetro"),
        ("kgf", "Kilograma-força"),
        ("°C", "Graus Celsius"),
        ("°", "Graus"),
        ("UR", "Unidade Relativa"),
        ("HRC", "HRC"),
        ("HRB", "HRB"),
        ("HV", "Dureza Vickers"),  # Adicionando HV para Dureza Vickers
        ("mN", "MiliNewton"),  # Adicionando miliNewton
        ("%", "Percentual"),
        ("kg", "Kilograma"),
        ("min", "Minutos"),
        ("s", "Segundos"),
        ("h", "Horas"),
    ]

    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    ]

    TIPO_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
    ]

    TIPO_AVALIACAO_CHOICES = [
        ("dureza", "Dureza"),
        ("carga", "Carga"),
        ("dimensional", "Dimensional"),
        ("temperatura", "Temperatura"),
        ("tempo", "Tempo"),
        ("massa", "Massa"),
    ]

    codigo = models.CharField(
        max_length=50, unique=True, verbose_name="Código do Equipamento"
    )
    nome_equipamento = models.CharField(
        max_length=100, verbose_name="Nome do Equipamento"
    )
    capacidade_minima = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Capacidade de Medição Mínima"
    )
    capacidade_maxima = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Capacidade de Medição Máxima"
    )
    tolerancia_em_percentual = models.IntegerField(
        verbose_name="Tolerância em (%)", null=True, blank=True
    )  # Novo campo
    resolucao = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Resolução"
    )
    unidade_medida = models.CharField(
        max_length=10, choices=UNIDADE_MEDIDA_CHOICES, verbose_name="Unidade de Medida"
    )
    tolerancia_total_minima = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name="Tolerância Total Mínima da Medida a Ser Realizada",
    )
    frequencia_calibracao = models.PositiveIntegerField(
        verbose_name="Frequência de Calibração (meses)"
    )
    exatidao_requerida = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Exatidão Requerida",
        null=True,
        blank=True,
    )

    # Campos da antiga Equipamentos
    numero_serie = models.CharField(
        max_length=100, unique=True, verbose_name="Número de Série"
    )
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    fabricante = models.CharField(max_length=100, verbose_name="Fabricante")
    foto_equipamento = models.ImageField(
        upload_to="equipamentos/",
        null=True,
        blank=True,
        verbose_name="Foto do Equipamento",
    )
    responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsável",
    )
    proprietario = models.CharField(max_length=100, verbose_name="Proprietário")
    localizacao = models.CharField(max_length=100, verbose_name="Localização")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="ativo", verbose_name="Status"
    )
    data_ultima_calibracao = models.DateField(
        null=True, blank=True, verbose_name="Data da Última Calibração"
    )  # Novo campo
    tipo = models.CharField(
        max_length=3,
        choices=TIPO_CHOICES,
        default="nao",
        verbose_name="Equipamento por Faixa",
    )  # Novo campo
    faixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        # Novo campo
        null=True,
        blank=True,
        verbose_name="Faixa (%)",
    )
    tipo_avaliacao = models.CharField(
        max_length=20,
        choices=TIPO_AVALIACAO_CHOICES,
        default="deslocamento",
        verbose_name="Tipo de Avaliação",
    )  # Novo campo
    updated_at = models.DateTimeField(auto_now=True)
    alteracao = models.TextField(blank=True, null=True, verbose_name="Última Alteração")

    def save(self, *args, **kwargs):
        alteracoes = []
        if self.pk:  # Se o registro já existir
            original = TabelaTecnica.objects.get(pk=self.pk)

            # Verificar alterações campo por campo
            campos_para_verificar = [
                "nome_equipamento",
                "capacidade_minima",
                "capacidade_maxima",
                "resolucao",
                "tolerancia_em_percentual",
                "unidade_medida",
                "tolerancia_total_minima",
                "frequencia_calibracao",
                "exatidao_requerida",
                "numero_serie",
                "modelo",
                "fabricante",
                "foto_equipamento",
                "responsavel",
                "proprietario",
                "localizacao",
                "status",
                "data_ultima_calibracao",
                "tipo",
                "faixa",
                "tipo_avaliacao",
            ]

            for campo in campos_para_verificar:
                valor_original = getattr(original, campo)
                valor_atual = getattr(self, campo)
                if valor_original != valor_atual:
                    alteracoes.append(
                        f"{campo.replace('_', ' ').capitalize()} alterado de '{valor_original}' para '{valor_atual}'"
                    )

        # Atualizar campo de alteração
        if alteracoes:
            self.alteracao = "; ".join(alteracoes)

        # Formatações específicas
        if self.codigo:
            self.codigo = self.codigo.upper()
        if self.modelo:
            self.modelo = self.modelo.upper()
        if self.nome_equipamento:
            self.nome_equipamento = self.nome_equipamento.title()
        if self.proprietario:
            self.proprietario = self.proprietario.title()
        if self.localizacao:
            self.localizacao = self.localizacao.title()
        if self.fabricante:
            self.fabricante = self.fabricante.title()

        # Lógica de exatidão requerida
        faixa = Decimal(self.faixa or 0)
        tolerancia = Decimal(self.tolerancia_em_percentual or 0)

        if self.tipo == "sim" and faixa > 0 and tolerancia > 0:
            self.exatidao_requerida = faixa * (tolerancia / Decimal(100))
        elif self.tolerancia_total_minima:
            self.exatidao_requerida = self.tolerancia_total_minima / Decimal(2)
        else:
            self.exatidao_requerida = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome_equipamento}"
