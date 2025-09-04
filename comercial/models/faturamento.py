from django.db import models
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from comercial.models.clientes import Cliente  # ajuste conforme o path real


class FaturamentoRegistro(models.Model):
    TIPO_CHOICES = [
    ("Venda", "Venda"),
    ("Devolução", "Devolução"),
]

    nfe = models.CharField("NF-e", max_length=50, null=True, blank=True)

    # Padrão brasileiro dd/mm/yyyy (armazenado como string)
    ocorrencia = models.DateField(blank=True, null=True)    
    cliente_codigo = models.CharField("Código do Cliente", max_length=50, null=True, blank=True)
 
    cliente = models.CharField("Cliente", max_length=200, null=True, blank=True)
    valor_frete = models.DecimalField("Valor Frete", max_digits=12, decimal_places=2, null=True, blank=True)

    item_codigo = models.CharField("Código do Item", max_length=100, null=True, blank=True)

    # Quantidade inteira (sem casas decimais)
    item_quantidade = models.IntegerField("Quantidade", null=True, blank=True)

    item_valor_unitario = models.DecimalField("Valor Unitário", max_digits=14, decimal_places=4, null=True, blank=True)
    item_ipi = models.DecimalField("IPI (%)", max_digits=6, decimal_places=2, null=True, blank=True)
    perc_icms = models.DecimalField("ICMS (%) (NF)", max_digits=6, decimal_places=2, null=True, blank=True)

    # Campos calculados
    valor_total = models.DecimalField("Valor Total", max_digits=16, decimal_places=2, null=True, blank=True)
    valor_total_com_ipi = models.DecimalField("Valor Total c/ IPI", max_digits=16, decimal_places=2, null=True, blank=True)
    tipo = models.CharField(
            "Tipo",
            max_length=20,
            choices=TIPO_CHOICES,
            default="Venda"
        )

    cliente_vinculado = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faturamentos",
        verbose_name="Cliente Vinculado"
    )

    # Idempotência
    chave_unica = models.CharField("Chave Única", max_length=255, unique=True, db_index=True)

    # Proteção opcional contra alterações
    congelado = models.BooleanField("Congelado (não atualizar via sync)", default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Faturamento (Registro)"
        verbose_name_plural = "Faturamento (Registros)"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.nfe or 'NF-e?'} - {self.item_codigo or 'item?'}"

    # --- helpers internos ---
    @staticmethod
    def _to_decimal(v, casas=2):
        if v is None or v == "":
            return None
        d = Decimal(str(v))
        q = Decimal("1." + ("0" * casas))
        return d.quantize(q, rounding=ROUND_HALF_UP)

    def _recalcular_totais(self):
        """
        Valor Total = quantidade * valor_unitario
        Valor Total c/ IPI = Valor Total * (1 + ipi/100)
        """
        q = self.item_quantidade or 0
        vu = Decimal("0") if self.item_valor_unitario is None else Decimal(self.item_valor_unitario)
        ipi = Decimal("0") if self.item_ipi is None else Decimal(self.item_ipi)

        total = Decimal(q) * vu
        total_c_ipi = total * (Decimal("1") + (ipi / Decimal("100")))

        # 2 casas para exibição/armazenamento financeiro
        self.valor_total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.valor_total_com_ipi = total_c_ipi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _calc_chave_unica(self) -> str:
        # inclui o cliente_codigo para evitar colisões
        base = (
            f"{self.nfe or ''}|{self.cliente_codigo or ''}|{self.cliente or ''}|"
            f"{self.ocorrencia or ''}|{self.item_codigo or ''}|"
            f"{self.item_valor_unitario or ''}|{self.item_quantidade or ''}|{self.valor_frete or ''}"
        )
        return hashlib.sha256(base.encode("utf-8")).hexdigest()
    
    def save(self, *args, **kwargs):
        # 🔄 Vincula automaticamente pelo CÓDIGO BM (Cliente.cod_bm) a partir de cliente_codigo
        if self.cliente_codigo:
            cod = str(self.cliente_codigo).strip().upper()
            self.cliente_vinculado = (
                Cliente.objects
                .filter(cod_bm__isnull=False)
                .filter(cod_bm__iexact=cod)
                .first()
            )
        else:
            self.cliente_vinculado = None

        # recalcula totais
        self._recalcular_totais()

        # recalcula chave idempotente
        nova = self._calc_chave_unica()
        if not self.chave_unica or self.chave_unica != nova:
            self.chave_unica = nova

        super().save(*args, **kwargs)

# comercial/models/faturamento.py

from django.db import models
from decimal import Decimal
import hashlib
from comercial.models.clientes import Cliente  # ajuste conforme o path real


class FaturamentoDuplicata(models.Model):
    """
    Duplicatas por NF (título/parcelas de uma Nota Fiscal).
    Vinculamos por 'nfe' (número da nota) e, quando possível,
    relacionamos ao Cliente usando o mesmo match do faturamento.
    """
    nfe = models.CharField("NF-e", max_length=50, db_index=True)
    numero_parcela = models.CharField("Parcela", max_length=50, null=True, blank=True)
    data_vencimento = models.DateField("Data de Vencimento", null=True, blank=True)
    valor_duplicata = models.DecimalField("Valor da Duplicata", max_digits=16, decimal_places=2)

    # Dados auxiliares para futura análise / relatórios
    cliente_codigo = models.CharField("Código do Cliente", max_length=50, null=True, blank=True)
    cliente = models.CharField("Cliente (texto livre)", max_length=200, null=True, blank=True)
    cliente_vinculado = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicatas_faturamento",
        verbose_name="Cliente Vinculado"
    )
    ocorrencia = models.DateField("Ocorrência (NF)", null=True, blank=True)
    
     # NOVOS CAMPOS FISCAIS
    natureza = models.CharField("Natureza da Operação", max_length=200, null=True, blank=True)
    cfop = models.CharField("CFOP", max_length=10, null=True, blank=True)
    valor_pis = models.DecimalField("Valor PIS", max_digits=16, decimal_places=2, null=True, blank=True)
    valor_cofins = models.DecimalField("Valor COFINS", max_digits=16, decimal_places=2, null=True, blank=True)
    valor_ipi = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_icms = models.DecimalField("Valor ICMS", max_digits=14, decimal_places=2, null=True, blank=True)  # ✅ novo campo


    # Idempotência por NF+parcela+data+valor
    chave_unica = models.CharField("Chave Única", max_length=255, unique=True, db_index=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Faturamento (Duplicata)"
        verbose_name_plural = "Faturamento (Duplicatas)"
        indexes = [
            models.Index(fields=["nfe", "data_vencimento"]),
        ]

    def __str__(self):
        p = self.numero_parcela or "—"
        return f"NF {self.nfe} • Parcela {p} • Vence {self.data_vencimento or '—'}"

    @staticmethod
    def _hash(nfe, numero_parcela, data_vencimento, valor_duplicata):
        dv = (data_vencimento.strftime("%Y-%m-%d") if data_vencimento else "")
        base = f"{nfe or ''}|{numero_parcela or ''}|{dv}|{valor_duplicata or ''}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        if not self.chave_unica:
            self.chave_unica = self._hash(
                self.nfe, self.numero_parcela, self.data_vencimento, self.valor_duplicata
            )
        # tenta vincular cliente pelo código (igual ao FaturamentoRegistro)
        if self.cliente_codigo:
            cod = str(self.cliente_codigo).strip().upper()
            self.cliente_vinculado = (
                Cliente.objects
                .filter(cod_bm__isnull=False)
                .filter(cod_bm__iexact=cod)
                .first()
            )
        super().save(*args, **kwargs)
