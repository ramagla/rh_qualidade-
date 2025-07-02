import os

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario


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
        upload_to="integracoes/",
        blank=True,
        null=True,
        verbose_name="PDF da Integração Assinada"
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
