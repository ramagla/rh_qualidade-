import os
from django.db import models
from django.utils import timezone
from .funcionario import Funcionario

class IntegracaoFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    grupo_whatsapp = models.BooleanField(default=False)
    requer_treinamento = models.BooleanField(default=False)
    treinamentos_requeridos = models.TextField(blank=True, null=True)
    data_integracao = models.DateField(default=timezone.now)
    pdf_integracao = models.FileField(upload_to='integracoes/', blank=True, null=True, verbose_name='PDF da Integração Assinada')

    @property
    def departamento(self):
        return self.funcionario.local_trabalho

    def save(self, *args, **kwargs):
        if self.pk:
            original = IntegracaoFuncionario.objects.get(pk=self.pk)
            if original.data_integracao != self.data_integracao:
                self.funcionario.data_integracao = self.data_integracao
                self.funcionario.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pdf_integracao and os.path.isfile(self.pdf_integracao.path):
            os.remove(self.pdf_integracao.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Integração - {self.funcionario.nome} ({self.data_integracao})"
