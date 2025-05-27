from django.db import models
from Funcionario.models import Funcionario
from datetime import datetime, timedelta, time

class AtrasoSaida(models.Model):
    TIPO_CHOICES = [
        ("atraso", "Atraso"),
        ("saida", "Saída Antecipada"),
        ("hora_extra", "Hora Extra"),  # ✅ Novo
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="ocorrencias_portaria")
    data = models.DateField()
    horario = models.TimeField(null=True, blank=True)
    hora_fim = models.TimeField(null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    observacao = models.TextField(blank=True, null=True)
    utilizado_no_banco = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atraso ou Saída Antecipada"
        verbose_name_plural = "Atrasos e Saídas Antecipadas"
        ordering = ["-data", "-horario"]

    def __str__(self):
        return f"{self.funcionario.nome} - {self.get_tipo_display()} em {self.data}"

    def calcular_duracao(self):
        """
        Retorna timedelta do atraso/saída considerando tolerância:
        - atraso: 10 min após entrada padrão 07:00
        - saída: 10 min antes de 16:48 (com desconto de almoço)
        """
        entrada_padrao = time(7, 0)
        saida_padrao = time(16, 48)
        tolerancia = timedelta(minutes=10)

        if not self.horario or self.tipo == "hora_extra":
            return timedelta(0)

        if self.tipo == "atraso":
            limite_atraso = (datetime.combine(self.data, entrada_padrao) + tolerancia).time()
            if self.horario > limite_atraso:
                atraso = datetime.combine(datetime.min, self.horario) - datetime.combine(datetime.min, limite_atraso)
                return atraso

        elif self.tipo == "saida":
            limite_saida = (datetime.combine(self.data, saida_padrao) - tolerancia).time()
            if self.horario < limite_saida:
                saida_antecipada = datetime.combine(datetime.min, limite_saida) - datetime.combine(datetime.min, self.horario)
                if self.horario < time(12, 0):  # desconto almoço
                    saida_antecipada -= timedelta(minutes=60)
                return max(saida_antecipada, timedelta(0))

        return timedelta(0)



    def calcular_duracao_formatada(self):
        d = self.calcular_duracao()
        total_min = int(d.total_seconds() // 60)
        return f"{total_min//60:02d}:{total_min%60:02d}"
