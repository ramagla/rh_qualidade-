from django.db import models
from Funcionario.models import Funcionario
from datetime import timedelta



class TabelaTecnica(models.Model):
    UNIDADE_MEDIDA_CHOICES = [
        ('mm', 'Milímetros'),
        ('kg.cm', 'Kilograma-centímetro'),
        ('kgf', 'Kilograma-força'),
        ('°C', 'Graus Celsius'),
        ('°', 'Graus'),
        ('UR', 'Unidade Relativa'),
        ('HCR', 'HCR'),
        ('HRB', 'HRB'),
        ('%', "Percentual")
    ]

    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código do Equipamento")
    nome_equipamento = models.CharField(max_length=100, verbose_name="Nome do Equipamento")
    capacidade_minima = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Capacidade de Medição Mínima")
    capacidade_maxima = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Capacidade de Medição Máxima")
    tolerancia_em_percentual = models.IntegerField(verbose_name="Tolerância em (%)", null=True, blank=True)  # Novo campo
    resolucao = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Resolução")
    unidade_medida = models.CharField(max_length=10, choices=UNIDADE_MEDIDA_CHOICES, verbose_name="Unidade de Medida")
    tolerancia_total_minima = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Tolerância Total Mínima da Medida a Ser Realizada")
    frequencia_calibracao = models.PositiveIntegerField(verbose_name="Frequência de Calibração (meses)")
    exatidao_requerida = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Exatidão Requerida", null=True, blank=True)

     # Campos da antiga Equipamentos
    numero_serie = models.CharField(max_length=100, unique=True, verbose_name="Número de Série")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    fabricante = models.CharField(max_length=100, verbose_name="Fabricante")
    foto_equipamento = models.ImageField(upload_to='equipamentos/', null=True, blank=True, verbose_name="Foto do Equipamento")
    responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsável"
    )
    proprietario = models.CharField(max_length=100, verbose_name="Proprietário")
    localizacao = models.CharField(max_length=100, verbose_name="Localização")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name="Status"
    )
    data_ultima_calibracao = models.DateField(null=True, blank=True, verbose_name="Data da Última Calibração")  # Novo campo

        
    def save(self, *args, **kwargs):
        # Atualiza o valor de Exatidão Requerida antes de salvar
        if self.tolerancia_total_minima:
            self.exatidao_requerida = self.tolerancia_total_minima / 2
        super().save(*args, **kwargs)

    # @property
    # def proxima_calibracao(self):
    #     if self.data_ultima_calibracao and self.frequencia_calibracao:
    #         return self.data_ultima_calibracao + timedelta(days=(self.frequencia_calibracao * 30))
    #     return None


    def __str__(self):
        return f"{self.codigo} - {self.nome_equipamento}"
