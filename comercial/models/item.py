
from django.db import models
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado  # já deve estar importado

class Item(models.Model):
    STATUS_CHOICES = [
    ("Ativo", "Ativo"),
    ("Inativo", "Inativo"),
]
    

    TIPO_ITEM_CHOICES = [
    ("Cotacao", "Cotação"),
    ("Corrente", "Corrente"),
]

    tipo_item = models.CharField("Tipo de Item", max_length=20, choices=TIPO_ITEM_CHOICES, default="Cotacao")
    cliente = models.ForeignKey("comercial.Cliente", on_delete=models.CASCADE, related_name="itens")
    codigo = models.CharField("Código Interno", max_length=50, unique=True)  # ⬅️ unique=True
    descricao = models.CharField("Descrição", max_length=255, blank=True, null=True)  # obrigatório
    ncm = models.CharField("NCM", max_length=10, blank=True, null=True)               # obrigatório
    lote_minimo = models.PositiveIntegerField("Lote Mínimo")   # obrigatório
    ferramenta = models.ForeignKey("comercial.Ferramenta", on_delete=models.SET_NULL, null=True, blank=True, related_name="itens")
    codigo_cliente = models.CharField("Código no Cliente", max_length=50, blank=True, null=True)
    descricao_cliente = models.CharField("Descrição no Cliente", max_length=255, blank=True, null=True)
    ipi = models.DecimalField("IPI (%)", max_digits=5, decimal_places=2, blank=True, null=True)
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default="Ativo")
    # switches
    seguranca_mp = models.BooleanField("Possui MP", default=False)
    seguranca_ts = models.BooleanField("Possui TS", default=False)
    seguranca_m1 = models.BooleanField("Possui M1", default=False)
    seguranca_l1 = models.BooleanField("Possui L1", default=False)
    seguranca_l2 = models.BooleanField("Possui L2", default=False)

    # imagens
    simbolo_mp = models.ImageField("Imagem MP", upload_to="itens/simbolos/", blank=True, null=True)
    simbolo_ts = models.ImageField("Imagem TS", upload_to="itens/simbolos/", blank=True, null=True)
    simbolo_m1 = models.ImageField("Imagem M1", upload_to="itens/simbolos/", blank=True, null=True)
    simbolo_l1 = models.ImageField("Imagem L1", upload_to="itens/simbolos/", blank=True, null=True)
    simbolo_l2 = models.ImageField("Imagem L2", upload_to="itens/simbolos/", blank=True, null=True)

    automotivo_oem = models.BooleanField("Automotivo OEM", default=False)
    requisito_especifico = models.BooleanField("Requisito Específico Cliente?", default=False)
    item_seguranca = models.BooleanField("É Item de Segurança?", default=False)
    codigo_desenho = models.CharField("Código do Desenho", max_length=50, blank=True, null=True)
    codigo_amostra = models.CharField("Código de Amostra", max_length=50, blank=True, null=True)

    desenho = models.FileField("Desenho", upload_to="itens/desenhos/", blank=True, null=True)
    revisao = models.CharField("Revisão", max_length=10, blank=True, null=True)
    data_revisao = models.DateField("Data da Revisão", blank=True, null=True)
    fontes_homologadas = models.ManyToManyField(
        FornecedorQualificado,
        verbose_name="Fontes Homologadas",
        blank=True,
        related_name="itens_homologados"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cliente', 'codigo']  # ⬅️ remove o unique_together

    def save(self, *args, **kwargs):
        if self.codigo_desenho:
            self.codigo_desenho = self.codigo_desenho.upper()

        if self.codigo_amostra:
            self.codigo_amostra = self.codigo_amostra.upper()

        if self.revisao:
            self.revisao = self.revisao.upper()

        if self.codigo:
            self.codigo = self.codigo.upper()  # ✅ CORREÇÃO AQUI

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.codigo}"
