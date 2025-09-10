from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default="MP")
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
    hash_consolidacao = models.CharField(max_length=64, blank=True)

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
    codigo_item = models.CharField(max_length=60)
    descricao = models.CharField(max_length=255, blank=True)
    etiqueta = models.CharField(max_length=100, blank=True)  # QRCode/etiqueta existente
    unidade = models.CharField(max_length=10, blank=True)
    local = models.CharField(max_length=60, blank=True)
    fornecedor = models.CharField(max_length=120, blank=True, default="")
    estoque_erp = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    quantidade_consolidada = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        # 🔁 Sem UniqueConstraint fixa; índice para busca rápida por etiqueta no inventário
        indexes = [
            models.Index(fields=["inventario", "etiqueta"], name="idx_invitem_inv_etq"),
        ]

    def clean(self):
        """
        Unicidade condicional:
        - MP: etiqueta (não vazia) NÃO pode repetir dentro do mesmo inventário;
        - PA: repetição permitida (vamos somar nas contagens).
        """
        super().clean()
        inv = getattr(self, "inventario", None)
        # normalização mínima antes da validação
        if isinstance(self.etiqueta, str):
            self.etiqueta = self.etiqueta.strip().upper()

        if self.etiqueta and inv and inv.tipo == "MP":
            qs = InventarioItem.objects.filter(inventario=inv, etiqueta=self.etiqueta)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"etiqueta": "Etiqueta já registrada neste inventário para Matéria-prima."})

    def save(self, *args, **kwargs):
        # 🔒 normalização
        for attr in ("codigo_item", "fornecedor", "local", "etiqueta"):
            val = getattr(self, attr, None)
            if isinstance(val, str):
                setattr(self, attr, val.strip().upper())
        # ✅ validação de negócio (inclui unicidade condicional)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo_item} - {self.etiqueta or ''}"


class Contagem(models.Model):
    ORDEM_CHOICES = [(1, "Primeira"), (2, "Segunda"), (3, "Terceira")]
    inventario_item = models.ForeignKey(InventarioItem, on_delete=models.CASCADE, related_name="contagens")
    ordem = models.PositiveSmallIntegerField(choices=ORDEM_CHOICES)
    quantidade = models.DecimalField(max_digits=14, decimal_places=4)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_hora = models.DateTimeField(auto_now_add=True)
    origem_qrcode = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("inventario_item", "ordem")

    def __str__(self):
        return f"{self.inventario_item.codigo_item or '-'} / {self.inventario_item.etiqueta or '-'}"


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
    formato = models.CharField(max_length=20, default="CSV")
    arquivo = models.FileField(upload_to="inventarios/exportacoes/", blank=True)

    class Meta:
        pass
