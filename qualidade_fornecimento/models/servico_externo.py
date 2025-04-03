from django.db import models
from datetime import timedelta, date

class ServicoExterno(models.Model):
    STATUS_CHOICES = [
        ("Ok", "Ok"),
        ("Nok", "Nok"),
    ]

    STATUS2_CHOICES = [
        ("OK", "OK"),
        ("Atenção Saldo", "Atenção Saldo"),
        ("Saldo maior que o enviado", "Saldo maior que o enviado"),
    ]

    IQF_CHOICES = [
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
    ]

    pedido = models.CharField(max_length=100)  # Pedido + guia de banho
    codigo_bm = models.CharField("Código da Peça", max_length=100)
    fornecedor = models.CharField(max_length=255)
    lead_time = models.PositiveIntegerField(help_text="Prazo de entrega em dias")
    quantidade_enviada = models.DecimalField(max_digits=10, decimal_places=2)
    data_envio = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    data_retorno = models.DateField(blank=True, null=True)

    # Dias 1 a 31 – valores de retorno parciais
    dias = models.JSONField("Retornos Diários", default=dict)  # Ex: {"1": 0, "2": 5, ..., "31": 0}

    total_retornado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status2 = models.CharField(max_length=50, choices=STATUS2_CHOICES, blank=True)
    iqf = models.CharField(max_length=20, choices=IQF_CHOICES, blank=True, null=True)
    prev_entrega = models.DateField(blank=True, null=True)
    atraso_dias = models.PositiveIntegerField(blank=True, null=True)
    ip = models.PositiveIntegerField("Índice de Pontualidade", blank=True, null=True)
    observacao = models.TextField(blank=True)

    def calcular_totais(self):
        self.total_retornado = sum(self.dias.get(str(d), 0) for d in range(1, 32))

        # Status2
        if self.total_retornado == self.quantidade_enviada:
            self.status2 = "OK"
        elif self.total_retornado < self.quantidade_enviada:
            self.status2 = "Atenção Saldo"
        else:
            self.status2 = "Saldo maior que o enviado"

        # Previsão de entrega
        self.prev_entrega = self.data_envio + timedelta(days=self.lead_time)

        # Atraso
        if self.data_retorno and self.data_retorno > self.prev_entrega:
            self.atraso_dias = (self.data_retorno - self.prev_entrega).days
        else:
            self.atraso_dias = 0

        # IP – Índice de Pontualidade
        if self.atraso_dias >= 21:
            self.ip = 30
        elif self.atraso_dias >= 16:
            self.ip = 20
        elif self.atraso_dias >= 11:
            self.ip = 15
        elif self.atraso_dias >= 7:
            self.ip = 10
        elif self.atraso_dias >= 4:
            self.ip = 5
        elif self.atraso_dias >= 1:
            self.ip = 2
        else:
            self.ip = 0

    def save(self, *args, **kwargs):
        self.calcular_totais()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pedido} - {self.fornecedor}"
