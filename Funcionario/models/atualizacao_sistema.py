from django.db import models
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import User


class AtualizacaoSistema(models.Model):
    STATUS_CHOICES = [
        ("concluido", "Concluído"),
        ("em_andamento", "Em andamento"),
        ("cancelado", "Cancelado"),
    ]

    titulo = models.CharField(max_length=100)
    descricao = CKEditor5Field(config_name="default")
    previsao = models.DateField()
    versao = models.CharField(
        max_length=20,
        verbose_name="Versão (ex: 1.6.5)",
        help_text="Informe no formato MAJOR.MINOR.PATCH (ex: 1.6.5)"
    )

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


class AtualizacaoLida(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    atualizacao = models.ForeignKey(AtualizacaoSistema, on_delete=models.CASCADE)
    data_leitura = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'atualizacao')
