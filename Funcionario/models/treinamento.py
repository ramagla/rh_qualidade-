import os
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from .funcionario import Funcionario

class Treinamento(models.Model):
    TIPO_TREINAMENTO_CHOICES = [
        ('interno', 'Interno'),
        ('externo', 'Externo'),
    ]
    
    CATEGORIA_CHOICES = [
        ('capacitacao', 'Capacitação'),
        ('tecnico', 'Técnico'),
        ('graduacao', 'Graduação'),
        ('pos-graduacao', 'Pos-graduacao'),
        ('treinamento', 'Treinamento'),
        ('divulgacao', 'Divulgação'),
    ]
    
    STATUS_CHOICES = [
        ('concluido', 'Concluído'),
        ('trancado', 'Trancado'),
        ('cursando', 'Cursando'),
        ('requerido', 'Requerido'),
    ]

    SITUACAO_CHOICES = [
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='treinamentos')
    tipo = models.CharField(max_length=50, choices=TIPO_TREINAMENTO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    nome_curso = models.CharField(max_length=100)
    instituicao_ensino = models.CharField(max_length=255, default='Bras-Mol')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='cursando')  # Campo de status
    data_inicio = models.DateField()
    data_fim = models.DateField()
    carga_horaria = models.CharField(max_length=50)
    anexo = models.FileField(upload_to='certificados/', blank=True, null=True)
    descricao = CKEditor5Field(config_name='default', blank=True, null=True )
    situacao = models.CharField(
        max_length=50,
        choices=SITUACAO_CHOICES,
        blank=True,
        null=True,
        help_text="Campo exibido apenas para treinamentos requeridos."
    )

    def __str__(self):
        return self.nome_curso
    
    def save(self, *args, **kwargs):
        if self.status != 'requerido':
            self.situacao = None  # Remove valor caso status não seja 'requerido'
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Remove o arquivo de mídia associado antes de excluir o registro
        if self.anexo:
            if os.path.isfile(self.anexo.path):
                os.remove(self.anexo.path)
        super().delete(*args, **kwargs)
