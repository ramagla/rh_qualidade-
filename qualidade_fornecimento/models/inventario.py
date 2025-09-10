from django.conf import settings
from django.db import models
from django.utils import timezone

class Inventario(models.Model):
    STATUS_CHOICES = [
        ("ABERTO", "Aberto"),
        ("EM_CONTAGEM_1", "Em 1ª Contagem"),
        ("EM_CONTAGEM_2", "Em 2ª Contagem"),
        ("EM_CONFERENCIA", "Em Confronto/Conferência"),
        ("DIVERGENTE", "Divergente"),
        ("CONSOLIDADO", "Consolidado"),
        ("EXPORTADO", "Exportado"),
    ]
    TIPO_CHOICES = [
        ("MP", "Matéria-prima"),
        ("PA", "Produto acabado"),
    ]

    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    data_corte = models.DateField()
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default="MP")  # 👈 novo
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ABERTO")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventarios_criados"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventarios_atualizados"
    )

    consolidado_em = models.DateTimeField(null=True, blank=True)
    consolidado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="inventarios_consolidados"
    )
    hash_consolidacao = models.CharField(max_length=64, blank=True)  # opcional

    class Meta:
        permissions = [
            ("consolidar_inventario", "Pode consolidar inventário"),
            ("exportar_inventario", "Pode exportar inventário"),
        ]

    def marcar_consolidado(self, user):
        self.status = "CONSOLIDADO"
        self.consolidado_em = timezone.now()
        self.consolidado_por = user
        self.save(update_fields=["status", "consolidado_em", "consolidado_por"])

    def __str__(self):
        return f"{self.titulo} ({self.get_status_display()})"

class InventarioItem(models.Model):
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name="itens")
    # Relacione com seu modelo de item/etiqueta TB050 conforme seu projeto:
    # Ex.: relacao_tb050 = models.ForeignKey(RelacaoMateriaPrima, on_delete=models.PROTECT)
    codigo_item = models.CharField(max_length=60)
    descricao = models.CharField(max_length=255, blank=True)
    etiqueta = models.CharField(max_length=100, blank=True)  # QRCode/etiqueta existente
    unidade = models.CharField(max_length=10, blank=True)
    local = models.CharField(max_length=60, blank=True)

    estoque_erp = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    quantidade_consolidada = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo_item} - {self.etiqueta or ''}"

class Contagem(models.Model):
    ORDEM_CHOICES = [
        (1, "Primeira"),
        (2, "Segunda"),
        (3, "Terceira"),
    ]
    inventario_item = models.ForeignKey(InventarioItem, on_delete=models.CASCADE, related_name="contagens")
    ordem = models.PositiveSmallIntegerField(choices=ORDEM_CHOICES)
    quantidade = models.DecimalField(max_digits=14, decimal_places=4)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_hora = models.DateTimeField(auto_now_add=True)
    origem_qrcode = models.CharField(max_length=120, blank=True)  # valor lido do QR

    class Meta:
        unique_together = ("inventario_item", "ordem")

class Divergencia(models.Model):
    inventario_item = models.OneToOneField(InventarioItem, on_delete=models.CASCADE, related_name="divergencia")
    qtd_contagem1 = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    qtd_contagem2 = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    qtd_contagem3 = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    houve_divergencia = models.BooleanField(default=False)
    resolvido_por_ajuste = models.BooleanField(default=False)
    justificativa_ajuste = models.TextField(blank=True)
    resolvido_em = models.DateTimeField(null=True, blank=True)
    resolvido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="divergencias_resolvidas"
    )

class InventarioExportacao(models.Model):
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name="exportacoes")
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    formato = models.CharField(max_length=20, default="CSV")  # CSV/TXT/JSON
    arquivo = models.FileField(upload_to="inventarios/exportacoes/", blank=True)

    class Meta:
        pass