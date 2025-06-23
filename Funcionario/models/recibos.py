# rh_qualidade/models/recibos.py

from django.db import models
from django.contrib.auth.models import User
from Funcionario.models import Funcionario

class ReciboPagamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='recibos_pagamento')
    nome_colaborador = models.CharField(max_length=150)  # redundância para facilitar filtros e relatórios
    mes_referencia = models.DateField(verbose_name="Mês de Referência")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_descontos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_liquido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to="recibos_pagamento/")

    data_importacao = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"{self.nome_colaborador} - {self.mes_referencia.strftime('%m/%Y')}"
