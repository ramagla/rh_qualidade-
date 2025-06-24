from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time
from django.utils import timezone

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

class Inspecao10(models.Model):  


    numero_op = models.CharField("Nº OP", max_length=20, default="000000")
    codigo_brasmol = models.CharField("Código Bras-Mol", max_length=50, default="SEM_CODIGO")
    data = models.DateField("Data", default=timezone.now)
    fornecedor = models.ForeignKey(FornecedorQualificado, on_delete=models.CASCADE)
    
    hora_inicio = models.TimeField("Hora - Início", default=time(0, 0, 0))
    hora_fim = models.TimeField("Hora - Fim", default=time(0, 0, 0))
    tempo_gasto = models.DurationField("Tempo Gasto", blank=True, null=True)

    quantidade_total = models.PositiveIntegerField("Quantidade Total", default=0)
    quantidade_nok = models.PositiveIntegerField("Quantidade Não OK", default=0)
    status = models.CharField("Status", max_length=30, blank=True, editable=False)

    observacoes = models.TextField("Observações", blank=True)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inspeção 10"
        verbose_name_plural = "Inspeções 10"

    def save(self, *args, **kwargs):
        if self.hora_inicio and self.hora_fim:
            inicio = datetime.combine(self.data, self.hora_inicio)
            fim = datetime.combine(self.data, self.hora_fim)
            if fim > inicio:
                self.tempo_gasto = fim - inicio
            else:
                self.tempo_gasto = timedelta()

        if self.quantidade_nok and self.quantidade_nok > 0:
            self.status = "FALHA DE BANHO"
        else:
            self.status = "OK"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fornecedor.nome} - {self.numero_op}"
