import os

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify

from .funcionario import Funcionario

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb

    def __call__(self, arquivo):
        if arquivo and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


def renomear_pdf_integracao(instance, filename):
    nome, extensao = os.path.splitext(filename)
    return os.path.join(
        "integracoes",
        f"integracao-{slugify(instance.funcionario.nome)}-{instance.funcionario.numero_registro}{extensao}"
    )

class IntegracaoFuncionario(models.Model):
    """
    Representa o registro da integração de um funcionário, incluindo grupo,
    treinamentos e documento assinado.
    """

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    grupo_whatsapp = models.BooleanField(
        default=False,
        verbose_name="Adicionado ao grupo de WhatsApp"
    )
    requer_treinamento = models.BooleanField(
        default=False,
        verbose_name="Requer Treinamento"
    )
    treinamentos_requeridos = models.TextField(
        blank=True,
        null=True,
        verbose_name="Treinamentos Requeridos"
    )
    data_integracao = models.DateField(
        default=timezone.now,
        verbose_name="Data da Integração"
    )
    pdf_integracao = models.FileField(
        upload_to=renomear_pdf_integracao,
        blank=True,
        null=True,
        verbose_name="PDF da Integração Assinada",
        validators=[MaxFileSizeValidator(5)],
    )

    @property
    def departamento(self):
        return self.funcionario.local_trabalho

    def save(self, *args, **kwargs):
        """
        Atualiza a data de integração também no modelo Funcionario quando alterada aqui.
        """
        if self.pk:
            original = IntegracaoFuncionario.objects.get(pk=self.pk)
            if original.data_integracao != self.data_integracao:
                self.funcionario.data_integracao = self.data_integracao
                self.funcionario.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Remove o arquivo do PDF do disco quando o registro for deletado.
        """
        if self.pdf_integracao and os.path.isfile(self.pdf_integracao.path):
            os.remove(self.pdf_integracao.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Integração - {self.funcionario.nome} ({self.data_integracao.strftime('%d/%m/%Y')})"

    class Meta:
        ordering = ["-data_integracao"]
        verbose_name_plural = "Integrações de Funcionários"
