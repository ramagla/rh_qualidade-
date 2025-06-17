
from django.db import models

class Item(models.Model):
    cliente = models.ForeignKey("comercial.Cliente", on_delete=models.CASCADE, related_name="itens")
    codigo = models.CharField("Código Interno", max_length=50, unique=True)  # ⬅️ unique=True
    descricao = models.CharField("Descrição", max_length=255)  # obrigatório
    ncm = models.CharField("NCM", max_length=10)               # obrigatório
    lote_minimo = models.PositiveIntegerField("Lote Mínimo")   # obrigatório
    ferramenta = models.ForeignKey("comercial.Ferramenta", on_delete=models.SET_NULL, null=True, blank=True, related_name="itens")
    codigo_cliente = models.CharField("Código no Cliente", max_length=50, blank=True, null=True)
    descricao_cliente = models.CharField("Descrição no Cliente", max_length=255, blank=True, null=True)
    ipi = models.DecimalField("IPI (%)", max_digits=5, decimal_places=2, blank=True, null=True)

    automotivo_oem = models.BooleanField("Automotivo OEM", default=False)
    requisito_especifico = models.BooleanField("Requisito Específico Cliente?", default=False)
    item_seguranca = models.BooleanField("É Item de Segurança?", default=False)

    desenho = models.FileField("Desenho", upload_to="itens/desenhos/", blank=True, null=True)
    revisao = models.CharField("Revisão", max_length=10, blank=True, null=True)
    data_revisao = models.DateField("Data da Revisão", blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cliente', 'codigo']  # ⬅️ remove o unique_together


    def __str__(self):
        return f"{self.codigo} – {self.descricao}"
