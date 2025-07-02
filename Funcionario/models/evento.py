from django.db import models


class Evento(models.Model):
    """
    Representa um evento do calendário institucional, como feriados,
    auditorias, avaliações e outros.
    """

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

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título do Evento"
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    data_inicio = models.DateField(
        verbose_name="Data de Início"
    )
    data_fim = models.DateField(
        verbose_name="Data de Fim"
    )
    cor = models.CharField(
        max_length=7,
        default="#3788d8",
        verbose_name="Cor (hexadecimal)"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_EVENTO,
        default="avaliacao_desempenho",
        verbose_name="Tipo de Evento"
    )

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ["data_inicio"]
        verbose_name_plural = "Eventos"
