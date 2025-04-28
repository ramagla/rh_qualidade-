# Arquivo: materiaPrima_catalogo.py
from django.db import models

TIPO_MATERIA_PRIMA = [
    ("Materia-Prima", "Matéria-Prima"),
    ("Tratamento", "Tratamento"),
]


class MateriaPrimaCatalogo(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.TextField()
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    classe = models.CharField(max_length=50, blank=True, null=True)
    norma = models.CharField(max_length=100, blank=True, null=True)
    bitola = models.CharField(max_length=50, blank=True, null=True)
    largura = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Largura"
    )

    tipo = models.CharField(
        max_length=50, choices=TIPO_MATERIA_PRIMA, default="Materia-Prima"
    )

    tipo_abnt = models.CharField(  # Novo Campo
        max_length=100, blank=True, null=True, verbose_name="Tipo ABNT"
    )

    tolerancia = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Tolerância"
    )
    tolerancia_largura = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Tolerância Largura"
    )

    atualizado_em = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        import re

        if not self.bitola and self.descricao:
            match = re.search(r"Ø([\d,.]+)", self.descricao)
            if match:
                self.bitola = match.group(1).replace(",", ".").strip() + " mm"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao[:50]}"  # Se quiser limitar para 50 caracteres
