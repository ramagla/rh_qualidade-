from decimal import Decimal
from django.db import models
from django.apps import apps  # <-- Importa o apps para uso dinâmico
from Funcionario.models import Funcionario
from django_ckeditor_5.fields import CKEditor5Field
from dateutil.relativedelta import relativedelta
import calendar
import os
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

def renomear_anexo_calibracao(instance, filename):
    nome, ext = os.path.splitext(filename)
    dispositivo = slugify(getattr(instance.codigo_dispositivo, "codigo", "") or "dispositivo")
    data = instance.data_afericao.strftime("%Y%m%d") if instance.data_afericao else "semdata"
    return os.path.join("metrologia", "calibracoes", f"calibracao-{dispositivo}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if arquivo and isinstance(arquivo, UploadedFile) and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb

class CalibracaoDispositivo(models.Model):
    STATUS_CHOICES = [
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
    ]
    
    calibracao_cliente = models.BooleanField(
            default=False,
            verbose_name="Calibração feita pelo cliente"
        )
    
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
    observacoes = CKEditor5Field("Observações gerais da calibração", blank=True, null=True)

    anexo = models.FileField(
            upload_to=renomear_anexo_calibracao,
            null=True,
            blank=True,
            verbose_name="Anexo",
            validators=[MaxFileSizeValidator(5)]
        )
    
    def delete(self, *args, **kwargs):
        if self.anexo:
            self.anexo.delete(save=False)
        super().delete(*args, **kwargs)
        
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

    def get_proxima_calibracao(self, frequencia_meses: int):
            """Retorna a próxima calibração no último dia do mês."""
            if not self.data_afericao:
                return None
            proxima = self.data_afericao + relativedelta(months=frequencia_meses)
            ultimo_dia = calendar.monthrange(proxima.year, proxima.month)[1]
            return proxima.replace(day=ultimo_dia)
    
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
