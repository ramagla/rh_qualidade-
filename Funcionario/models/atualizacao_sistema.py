from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.timezone import now


class AtualizacaoSistema(models.Model):
    STATUS_CHOICES = [
        ('concluido', 'Concluído'),
        ('em_andamento', 'Em andamento'),
        ('cancelado', 'Cancelado'),
    ]

    titulo = models.CharField(max_length=100)
    descricao = CKEditor5Field(config_name='default')     
    previsao = models.DateField()
    versao = models.CharField(max_length=20)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='em_andamento',
    )
    data_termino = models.DateField(default=now, blank=True, null=True)  # Valor padrão definido como a data atual


    def __str__(self):
        return f"{self.versao} - {self.titulo}"
