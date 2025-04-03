from django.db import models
from datetime import date

class MateriaPrima(models.Model):
    STATUS_CHOICES = [
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
    ]

    num_relatorio = models.PositiveIntegerField(unique=True, editable=False)
    num_rolo = models.PositiveIntegerField(unique=True, editable=False)
    data_entrada = models.DateField()
    fornecedor = models.CharField(max_length=255)
    nota_fiscal = models.CharField(max_length=50)
    num_certificado = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    bitola = models.CharField(max_length=50, blank=True)
    classe = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    data_prevista_entrega = models.DateField(blank=True, null=True)
    data_entrega_renegociada = models.DateField(blank=True, null=True)
    atraso_dias = models.IntegerField(blank=True, null=True)
    ip = models.PositiveIntegerField("Demérito (IP)", blank=True, null=True)
    anexo_certificado = models.FileField(upload_to="certificados_mp/", blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto incrementos simulados (ajustável se quiser usar sequência no banco)
        if not self.pk:
            ultima = MateriaPrima.objects.order_by('-num_relatorio').first()
            self.num_relatorio = ultima.num_relatorio + 1 if ultima else 40000
            self.num_rolo = ultima.num_rolo + 1 if ultima else 50000

        # Extração da bitola
        if self.codigo.startswith("F"):
            self.bitola = self.codigo
        elif "Ø" in self.codigo:
            try:
                pos = self.codigo.index("Ø")
                self.bitola = self.codigo[pos+1:pos+6].strip() + " MM"
            except Exception:
                self.bitola = ""
        else:
            self.bitola = ""

        # Cálculo do atraso
        hoje = date.today()
        if self.data_prevista_entrega:
            entrega = self.data_entrega_renegociada or self.data_prevista_entrega
            self.atraso_dias = (hoje - entrega).days if hoje > entrega else 0

        # Demérito IP conforme atraso
        if self.atraso_dias is not None:
            if self.atraso_dias >= 21:
                self.ip = 30
            elif self.atraso_dias >= 16:
                self.ip = 20
            elif self.atraso_dias >= 11:
                self.ip = 15
            elif self.atraso_dias >= 7:
                self.ip = 10
            elif self.atraso_dias >= 4:
                self.ip = 5
            elif self.atraso_dias >= 1:
                self.ip = 2
            else:
                self.ip = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.fornecedor}"
