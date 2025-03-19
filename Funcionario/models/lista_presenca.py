from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from .funcionario import Funcionario


class ListaPresenca(models.Model):
    TIPO_CHOICES = [
        ("Treinamento", "Treinamento"),
        ("Curso", "Curso"),
        ("Divulgacao", "Divulgação"),
        ("Conscientização", "Conscientização"),
    ]

    SITUACAO_CHOICES = [
        ("finalizado", "Finalizado"),
        ("em_andamento", "Em Andamento"),
    ]

    treinamento = models.CharField(max_length=255, choices=TIPO_CHOICES)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    instrutor = models.CharField(max_length=255)
    duracao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    necessita_avaliacao = models.BooleanField(default=False)
    lista_presenca = models.FileField(
        upload_to="listas_presenca/", null=True, blank=True
    )
    participantes = models.ManyToManyField(Funcionario, related_name="participantes")
    assunto = models.CharField(
        max_length=255, null=True, blank=True
    )  # Permite valores nulos
    descricao = CKEditor5Field(config_name="default")
    situacao = models.CharField(
        max_length=20, choices=SITUACAO_CHOICES, default="em_andamento"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def duracao_formatada(self):
        total_minutes = int(self.duracao * 60)  # Converte horas para minutos
        hours = total_minutes // 60  # Divide por 60 para obter as horas inteiras
        minutes = total_minutes % 60  # Resto da divisão para obter os minutos
        return f"{hours}h {minutes}m"

    def __str__(self):
        return f"Lista de Presença - {self.treinamento} ({self.data_inicio} - {self.data_fim})"
