# models/revisao_doc_leitura.py

from django.contrib.auth.models import User
from django.db import models
from Funcionario.models.documentos import RevisaoDoc

class RevisaoDocLeitura(models.Model):
    revisao = models.ForeignKey(RevisaoDoc, related_name="leituras", on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_leitura = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("revisao", "usuario")

    def __str__(self):
        return f"{self.usuario} leu {self.revisao}"
