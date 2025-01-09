from django.db import models

class Evento(models.Model):
    TIPOS_EVENTO = [
        ("avaliacao_desempenho", "Avaliação de Desempenho"),
        ("feriado", "Feriado"),
        ("ponte", "Ponte"),
        ("confraternizacao", "Confraternização"),
        ("recesso", "Recesso"),
        ("auditoria_sgs", "Auditoria SGS"),
        ("auditoria_interna", "Auditoria Interna"),
        ("sipat", "SIPAT"),
        ("inventario", "Inventário"),
    ]
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    cor = models.CharField(max_length=7, default='#3788d8')
    tipo = models.CharField(max_length=20, choices=TIPOS_EVENTO, default="avaliacao_desempenho")

    def __str__(self):
        return self.titulo
