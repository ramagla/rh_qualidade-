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
    norma = models.ForeignKey(
            "qualidade_fornecimento.NormaTecnica",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            verbose_name="Norma",
            related_name="materias_primas"
        )    
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

    tipo_material = models.CharField(
    max_length=100, blank=True, null=True, verbose_name="Tipo de Material"
    )


    atualizado_em = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        import re

        # Converter localização para maiúsculas
        if self.localizacao:
            self.localizacao = self.localizacao.upper()

        # Preencher a bitola a partir da descrição (se estiver vazia)
        if not self.bitola and self.descricao:
            match = re.search(r"Ø([\d,.]+)", self.descricao)
            if match:
                self.bitola = match.group(1).replace(",", ".").strip() + " mm"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descricao[:50]}"  # Se quiser limitar para 50 caracteres
