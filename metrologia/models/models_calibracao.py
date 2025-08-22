from django.db import models

from .models_tabelatecnica import TabelaTecnica
import os
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from dateutil.relativedelta import relativedelta

def renomear_certificado_calibracao(instance, filename):
    nome, ext = os.path.splitext(filename)
    codigo = slugify(getattr(instance.codigo, "codigo", "") or "equipamento")
    data = instance.data_calibracao.strftime("%Y%m%d") if instance.data_calibracao else "semdata"
    numero = slugify(instance.numero_certificado or "certificado")
    return os.path.join("calibracoes", f"certificado-{codigo}-{numero}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5): self.max_mb = max_mb
    def __call__(self, f):
        if f and isinstance(f, UploadedFile) and f.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other): return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


class Calibracao(models.Model):
    LABORATORIO_CHOICES = [
        ("Ceime", "Ceime"),
        ("Instemaq", "Instemaq"),
        ("Microoptica", "Microoptica"),
        ("Trescal", "Trescal"),
        ("Embracal", "Embracal"),
        ("Kratos", "Kratos"),
        ("Tecmetro", "Tecmetro"),
    ]

    codigo = models.ForeignKey(
        TabelaTecnica, on_delete=models.CASCADE, verbose_name="Código do Equipamento"
    )
    laboratorio = models.CharField(
        max_length=100,
        choices=LABORATORIO_CHOICES,  # Define as opções do select
        verbose_name="Laboratório",
    )
    numero_certificado = models.CharField(
        max_length=100, verbose_name="Número do Certificado"
    )
    erro_equipamento = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Erro do Equipamento (E)"
    )
    incerteza = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Incerteza (I)"
    )
    data_calibracao = models.DateField(
        verbose_name="Data da Calibração", null=True, blank=True
    )  # Novo campo
    certificado_anexo = models.FileField(
        upload_to=renomear_certificado_calibracao,
        null=True, blank=True,
        verbose_name="Certificado de Calibração",
        validators=[MaxFileSizeValidator(5)],
    )
    l = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="L", editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=[("Aprovado", "Aprovado"), ("Reprovado", "Reprovado")],
        editable=False,
    )
    def delete(self, *args, **kwargs):
        if self.certificado_anexo:
            self.certificado_anexo.delete(save=False)
        super().delete(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        # Calcula o valor de 'L'
        self.l = self.erro_equipamento + self.incerteza

        # Verifica exatidão requerida e define status
        exatidao_requerida = self.codigo.exatidao_requerida
        if self.l <= exatidao_requerida:
            self.status = "Aprovado"
        else:
            self.status = "Reprovado"

        # Salva a instância de Calibracao
        super().save(*args, **kwargs)

        # Atualiza a data da última calibração no modelo TabelaTecnica
        if self.status == "Aprovado" and self.data_calibracao:
            tabela_tecnica = self.codigo
            tabela_tecnica.data_ultima_calibracao = self.data_calibracao
            tabela_tecnica.save()

    def __str__(self):
        return f"{self.codigo} - {self.numero_certificado}"

    def get_proxima_calibracao(self, frequencia_meses: int):
            """Retorna a próxima calibração no último dia do mês."""
            if not self.data_calibracao:
                return None
            proxima = self.data_calibracao + relativedelta(months=frequencia_meses)
            ultimo_dia = calendar.monthrange(proxima.year, proxima.month)[1]
            return proxima.replace(day=ultimo_dia)