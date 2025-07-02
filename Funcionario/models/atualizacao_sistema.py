from django.db import models
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import User


class AtualizacaoSistema(models.Model):
    """Modelo que representa uma atualização do sistema com versão, descrição e status."""

    STATUS_CHOICES = [
        ("concluido", "Concluído"),
        ("em_andamento", "Em andamento"),
        ("cancelado", "Cancelado"),
    ]

    titulo = models.CharField(
        max_length=100,
        verbose_name="Título"
    )
    descricao = CKEditor5Field(
        config_name="default",
        verbose_name="Descrição"
    )
    previsao = models.DateField(
        verbose_name="Data de Previsão"
    )
    versao = models.CharField(
        max_length=20,
        verbose_name="Versão (ex: 1.6.5)",
        help_text="Informe no formato MAJOR.MINOR.PATCH (ex: 1.6.5)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="em_andamento",
        verbose_name="Status"
    )
    data_termino = models.DateField(
        default=now,
        blank=True,
        null=True,
        verbose_name="Data de Término"
    )
    arquivo_pdf = models.FileField(
        upload_to='atualizacoes/',
        blank=True,
        null=True,
        verbose_name="Arquivo PDF"
    )
    previa_versao = CKEditor5Field(
        config_name="default",
        blank=True,
        null=True,
        verbose_name="Prévia da Versão"
    )

    def __str__(self):
        return f"{self.versao} - {self.titulo}"

    class Meta:
        ordering = ['-previsao']
        verbose_name_plural = "Atualizações do Sistema"


class AtualizacaoLida(models.Model):
    """Registra quando um usuário leu uma atualização específica."""

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    atualizacao = models.ForeignKey(
        AtualizacaoSistema,
        on_delete=models.CASCADE,
        verbose_name="Atualização"
    )
    data_leitura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Leitura"
    )

    def __str__(self):
        return f"{self.usuario.username} leu {self.atualizacao.versao}"

    class Meta:
        unique_together = ('usuario', 'atualizacao')
        verbose_name_plural = "Atualizações Lidas"
