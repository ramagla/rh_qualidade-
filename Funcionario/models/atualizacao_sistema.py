from django.db import models
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field


class AtualizacaoSistema(models.Model):
    STATUS_CHOICES = [
        ("concluido", "Concluído"),
        ("em_andamento", "Em andamento"),
        ("cancelado", "Cancelado"),
    ]

    titulo = models.CharField(max_length=100)
    descricao = CKEditor5Field(config_name="default")
    previsao = models.DateField()
    versao = models.CharField(max_length=20)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="em_andamento",
    )
    # Valor padrão definido como a data atual
    data_termino = models.DateField(default=now, blank=True, null=True)
    arquivo_pdf = models.FileField(upload_to='atualizacoes/', blank=True, null=True)

    previa_versao = CKEditor5Field(
        config_name="default",
        blank=True,
        null=True,
        verbose_name="Prévia da Versão"
    )

    def __str__(self):
        return f"{self.versao} - {self.titulo}"
