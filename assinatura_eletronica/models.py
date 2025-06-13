from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class AssinaturaEletronica(models.Model):
    hash = models.CharField(max_length=64, unique=True)
    conteudo = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_assinatura = models.DateTimeField(default=now)
    origem_model = models.CharField(max_length=100)
    origem_id = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.origem_model} #{self.origem_id} - {self.usuario.username}"
