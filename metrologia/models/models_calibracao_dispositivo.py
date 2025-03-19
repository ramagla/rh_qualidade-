from decimal import Decimal
from django.db import models
from django.apps import apps  # <-- Importa o apps para uso dinâmico
from Funcionario.models import Funcionario

class CalibracaoDispositivo(models.Model):
    STATUS_CHOICES = [
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
    ]

    codigo_dispositivo = models.ForeignKey(
        'metrologia.Dispositivo',  # <-- lazy reference!
        on_delete=models.CASCADE,
        related_name="calibracoes",
        verbose_name="Código do Dispositivo",
    )
    instrumento_utilizado = models.ForeignKey(
        'metrologia.TabelaTecnica',  # <-- lazy reference!
        on_delete=models.SET_NULL,
        null=True,
        related_name="calibracoes_utilizadas",
        verbose_name="Instrumento Utilizado",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name="Status",
        blank=True,
        null=True,
    )
    data_afericao = models.DateField(verbose_name="Data da Aferição")
    nome_responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calibracoes_realizadas",
        verbose_name="Nome do Responsável",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def save(self, *args, **kwargs):
        # Atualiza a data_ultima_calibracao do Dispositivo associado
        if self.data_afericao:
            dispositivo = self.codigo_dispositivo
            if (
                dispositivo.data_ultima_calibracao is None
                or self.data_afericao > dispositivo.data_ultima_calibracao
            ):
                dispositivo.data_ultima_calibracao = self.data_afericao
                dispositivo.save()

        super().save(*args, **kwargs)

    def atualizar_status(self):
        """Atualiza o status com base nas aferições."""
        todas_aprovadas = all(
            afericao.status == "Aprovado" for afericao in self.afericoes.all()
        )
        self.status = "Aprovado" if todas_aprovadas else "Reprovado"
        self.save(update_fields=["status"])

    def __str__(self):
        return f"Calibração de {self.codigo_dispositivo.codigo} - {self.status}"

    @property
    def codigo_peca(self):
        if self.codigo_dispositivo and len(self.codigo_dispositivo.codigo) > 2:
            return self.codigo_dispositivo.codigo[:-2]
        return self.codigo_dispositivo.codigo


class Afericao(models.Model):
    calibracao_dispositivo = models.ForeignKey(
        "CalibracaoDispositivo",
        on_delete=models.CASCADE,
        related_name="afericoes",
    )
    cota = models.ForeignKey(
        'metrologia.Cota',  # <-- lazy reference!
        on_delete=models.CASCADE,
        related_name="afericoes"
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor da Aferição"
    )
    status = models.CharField(
        max_length=20,
        choices=[("Aprovado", "Aprovado"), ("Reprovado", "Reprovado")],
        verbose_name="Status",
        blank=True,
    )

    def save(self, *args, **kwargs):
        Cota = apps.get_model('metrologia', 'Cota')  # <-- Se quiser buscar algo da Cota
        if self.valor is not None and self.cota is not None:
            valor_minimo = Decimal(str(self.cota.valor_minimo))
            valor_maximo = Decimal(str(self.cota.valor_maximo))
            valor = Decimal(str(self.valor))

            if valor_minimo <= valor <= valor_maximo:
                self.status = "Aprovado"
            else:
                self.status = "Reprovado"
        else:
            self.status = "Reprovado"
        super().save(*args, **kwargs)
