from django.db import models
from metrologia.models import Dispositivo, TabelaTecnica
from .models_dispositivos import Dispositivo, Cota
from Funcionario.models import Funcionario

class CalibracaoDispositivo(models.Model):
    STATUS_CHOICES = [
        ('Aprovado', 'Aprovado'),
        ('Reprovado', 'Reprovado'),
    ]

    codigo_peca = models.CharField(
        max_length=50,
        verbose_name="Código da Peça",
        help_text="Referente ao campo código do modelo de dados Dispositivo sem os últimos 2 caracteres."
    )
    codigo_dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name="calibracoes",
        verbose_name="Código do Dispositivo"
    )
    instrumento_medicao = models.CharField(
        max_length=100,
        verbose_name="Instrumento de Medição",
        help_text="Referente ao campo nome_equipamento do modelo de dados TabelaTecnica."
    )
    afericao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Aferição"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name="Status"
    )
    instrumento_utilizado = models.ForeignKey(
        TabelaTecnica,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calibracoes_utilizadas",
        verbose_name="Instrumento Utilizado"
    )
    data_afericao = models.DateField(
        verbose_name="Data da Aferição"
    )
    nome_responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calibracoes_realizadas",
        verbose_name="Nome do Responsável"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    def save(self, *args, **kwargs):
        # Gera o código da peça baseado no código do dispositivo
        if self.codigo_dispositivo:
            self.codigo_peca = self.codigo_dispositivo.codigo[:-2]

        # Atualiza a data_ultima_calibracao do Dispositivo associado
        if self.data_afericao:
            dispositivo = self.codigo_dispositivo
            if dispositivo.data_ultima_calibracao is None or self.data_afericao > dispositivo.data_ultima_calibracao:
                dispositivo.data_ultima_calibracao = self.data_afericao
                dispositivo.save()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Calibração de {self.codigo_dispositivo.codigo} - {self.status}"
    
class Afericao(models.Model):
    calibracao_dispositivo = models.ForeignKey(
        'CalibracaoDispositivo',  # Relacionamento atrasado
        on_delete=models.CASCADE,
        related_name='afericoes'
    )
    cota = models.ForeignKey(Cota, on_delete=models.CASCADE, related_name='afericoes')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Aferição")
    status = models.CharField(
        max_length=20,
        choices=[('Aprovado', 'Aprovado'), ('Reprovado', 'Reprovado')],
        verbose_name="Status",
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.valor is not None and self.cota is not None:
            if self.cota.valor_minimo <= self.valor <= self.cota.valor_maximo:
                self.status = 'Aprovado'
            else:
                self.status = 'Reprovado'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Aferição {self.cota.numero} - {self.status}"
