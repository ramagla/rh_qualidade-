from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum, UniqueConstraint
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models.functions import Lower

User = get_user_model()


def _q(val: Optional[Decimal]) -> Decimal:
    """Quantiza Decimal para 3 casas (kg) com HALF_UP; trata None como 0."""
    if val is None:
        val = Decimal("0")
    return (Decimal(val) if isinstance(val, Decimal) else Decimal(str(val))).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )


class EstoqueIntermediario(models.Model):
    STATUS = [
        ("EM_FABRICA", "Em Fábrica"),
        ("RETORNADO", "Retornado"),
        ("CANCELADO", "Cancelado"),
    ]

    # Identificação / vínculos (cabeçalho do envio)
    op = models.CharField("OP", max_length=30, db_index=True)
    materia_prima = models.ForeignKey(
        "qualidade_fornecimento.MateriaPrimaCatalogo",
        on_delete=models.PROTECT,
        related_name="estoques_intermediarios",
        verbose_name="Matéria-prima",
    )

    # Planejado (para consumo por peça)
    qtde_op_prevista = models.DecimalField("Qtd MP prevista (kg)", max_digits=12, decimal_places=3)
    pecas_planejadas_op = models.PositiveIntegerField("Peças planejadas OP")

    # Totais (→ sempre recalculados a partir dos itens)
    enviado = models.DecimalField("Total enviado (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    retorno = models.DecimalField("Total retorno (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))

    # Apontamentos do processo (nível cabeçalho)
    sucata = models.DecimalField("Sucata (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    refugo = models.DecimalField("Refugo (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    pecas_apontadas = models.PositiveIntegerField("Peças apontadas", default=0)

    # Cálculos (persistidos para auditoria)
    consumo_inferido_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    consumo_balanca_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    consumo_real_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))

    # Configuração e controle
    tolerancia_sucata_percentual = models.DecimalField(
        "Tolerância de sucata (%)", max_digits=5, decimal_places=2, default=Decimal("3.00")
    )
    custo_kg = models.DecimalField("Custo por kg (opcional)", max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=12, choices=STATUS, default="EM_FABRICA", db_index=True)
    data_envio = models.DateTimeField(null=True, blank=True, db_index=True)
    data_retorno = models.DateTimeField(null=True, blank=True)

    responsavel_envio = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ei_responsavel_envio"
    )
    responsavel_retorno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ei_responsavel_retorno"
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ei_aprovou_excesso"
    )

    maquina = models.ForeignKey("tecnico.Maquina", on_delete=models.SET_NULL, null=True, blank=True)

    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="estoque_intermediario/%Y/%m/", blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ei_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ei_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    justificativa_excesso = models.TextField("Justificativa p/ excesso de sucata", blank=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("close_estoqueintermediario", "Pode fechar item do Estoque Intermediário"),
            ("export_estoqueintermediario", "Pode exportar Estoque Intermediário"),
        ]
        # + adicionar (unicidade da OP considerando EM_FABRICA e RETORNADO; case-insensitive)
        constraints = [
            UniqueConstraint(
                Lower("op"),
                condition=Q(status__in=("EM_FABRICA", "RETORNADO")),
                name="uniq_ei_op_em_fabrica_ou_retornado_ci",
            ),
        ]


    # --------- Propriedades / KPIs ---------
    @property
    def consumo_por_peca_planejado(self) -> Decimal:
        if not self.pecas_planejadas_op:
            return Decimal("0.000")
        return _q(self.qtde_op_prevista) / Decimal(self.pecas_planejadas_op)

    @property
    def consumo_previsto_planejado_kg(self) -> Decimal:
            """
            Previsto global (planejado +5%).
            """
            return _q(_q(self.qtde_op_prevista) * Decimal("1.05"))
    

    @property
    def consumo_previsto_ajustado_kg(self) -> Decimal:
        """
        Previsto ajustado à produção realizada (+5%).
        Fórmula: (qtde_op_prevista / peças_planejadas) * peças_apontadas * 1.05
        """
        if not self.pecas_planejadas_op:
            return Decimal("0.000")
        base = _q(
            _q(self.qtde_op_prevista)
            / Decimal(self.pecas_planejadas_op)
            * Decimal(self.pecas_apontadas or 0)
        )
        return _q(base * Decimal("1.05"))
    
    @property
    def saldo_kg(self) -> Decimal:
        """
        Saldo = Enviado - Previsto(kg +5%)
        """
        return _q(_q(self.enviado) - _q(self.previsto_kg))


    @property
    def comparativo_previsto(self) -> str:
        """
        Compara consumo_real_kg com o previsto_ajustado.
        Retorna: 'ACIMA' | 'ABAIXO' | 'DENTRO'
        """
        real = _q(self.consumo_real_kg)
        prev = _q(self.consumo_previsto_ajustado_kg)
        if real > prev:
            return "ACIMA"
        if real < prev:
            return "ABAIXO"
        return "DENTRO"
    
    @property
    def perc_sucata(self) -> Decimal:
        real = _q(self.consumo_real_kg)
        if real <= 0:
            return Decimal("0.00")
        return (self.sucata / real * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def desvio_balanco_percent(self) -> Decimal:
        # enviado ≈ retorno + consumo_real
        den = _q(self.enviado)
        if den <= 0:
            return Decimal("0.00")
        num = abs(_q(self.enviado) - (_q(self.retorno) + _q(self.consumo_real_kg)))
        return (num / den * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def dias_em_fabrica(self) -> int:
        ref = self.data_envio or self.created_at
        fim = timezone.now() if self.status == "EM_FABRICA" else (self.data_retorno or timezone.now())
        return max((fim.date() - ref.date()).days, 0)

    # --------- Cálculo / validação ---------
    def _atualizar_calculos(self):
        # 1) consumo inferido
        ci = _q(self.consumo_por_peca_planejado * Decimal(self.pecas_apontadas or 0))

        # 2) consumo balança (a partir dos totais dos itens)
        cb = _q(_q(self.enviado) - _q(self.retorno))
        if cb < 0:
            cb = Decimal("0.000")

        # 3) real
        cr = ci if ci >= cb else cb

        self.consumo_inferido_kg = ci
        self.consumo_balanca_kg = cb
        self.consumo_real_kg = cr

    def recalc_totais(self, save: bool = True):
        """Recalcula totais somando os itens."""
        agg = self.itens.aggregate(
            total_env=Sum("enviado"),
            total_ret=Sum("retorno"),
            total_suc=Sum("sucata"),
            total_ref=Sum("refugo"),
        )
        self.enviado = _q(agg["total_env"] or 0)
        self.retorno = _q(agg["total_ret"] or 0)
        self.sucata  = _q(agg["total_suc"] or 0)
        self.refugo  = _q(agg["total_ref"] or 0)

        self._atualizar_calculos()
        if save:
            self.save(update_fields=[
                "enviado","retorno","sucata","refugo",
                "consumo_inferido_kg","consumo_balanca_kg","consumo_real_kg","updated_at"
            ])


    def clean(self):
        if self.pecas_planejadas_op <= 0:
            raise ValidationError({"pecas_planejadas_op": "Peças planejadas deve ser > 0."})
        self._atualizar_calculos()

        if self.status == "RETORNADO":
            # Se retornado, validar sucata vs tolerância
            tol = (self.tolerancia_sucata_percentual or Decimal("3.00")).quantize(Decimal("0.01"))
            if self.perc_sucata > tol and not self.justificativa_excesso:
                raise ValidationError(
                    {"justificativa_excesso": f"Percentual de sucata {self.perc_sucata}% excede tolerância {tol}%. Informe justificativa."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OP {self.op} • {self.materia_prima} • {self.itens.count()} lote(s)"


class EstoqueIntermediarioItem(models.Model):
    """Item por lote/rolo dentro de um envio (cabeçalho)."""
    parent = models.ForeignKey(
        EstoqueIntermediario,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Envio",
    )
    lote = models.ForeignKey(
        "qualidade_fornecimento.RoloMateriaPrima",
        on_delete=models.PROTECT,
        related_name="ei_itens",
        verbose_name="Lote / Rolo",
    )
    tb050 = models.ForeignKey(
        "qualidade_fornecimento.RelacaoMateriaPrima",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ei_itens",
        verbose_name="TB050 (opcional)",
    )
    enviado = models.DecimalField("Enviado (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    retorno = models.DecimalField("Retorno (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    sucata  = models.DecimalField("Sucata (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    refugo  = models.DecimalField("Refugo (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    class Meta:
        ordering = ["id"]
        constraints = [
            UniqueConstraint(fields=["parent", "lote"], name="uniq_eiitem_parent_lote"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        from qualidade_fornecimento.models import RoloMateriaPrima, RelacaoMateriaPrima

        errors = {}

        # 🔹 Se veio LOTE e não veio TB050, puxa do lote sem acessar a relação diretamente
        if self.lote_id and not self.tb050_id:
            try:
                self.tb050_id = RoloMateriaPrima.objects.only("tb050_id").get(pk=self.lote_id).tb050_id
            except RoloMateriaPrima.DoesNotExist:
                pass  # deixa sem TB050; o form pode acusar depois

        # 🔹 TB050 precisa bater com a MP do cabeçalho (usa apenas IDs)
        if self.parent_id and self.tb050_id:
            mp_tb = (
                RelacaoMateriaPrima.objects.only("materia_prima_id")
                .filter(pk=self.tb050_id)
                .values_list("materia_prima_id", flat=True)
                .first()
            )
            if mp_tb and self.parent and mp_tb != self.parent.materia_prima_id:
                errors["tb050"] = "TB050 não corresponde à Matéria-prima do envio."

        # 🔹 Evita mesmo lote+OP aberto em outro cabeçalho (só quando já há parent_id)
        if self.parent_id and self.lote_id and self.parent and self.parent.op:
            dup_aberto = (
                EstoqueIntermediarioItem.objects.filter(
                    lote_id=self.lote_id,
                    parent__op=self.parent.op,
                    parent__status="EM_FABRICA",
                )
                .exclude(parent_id=self.parent_id)
                .exclude(pk=self.pk or 0)
                .exists()
            )
            if dup_aberto:
                errors["lote"] = "Este lote já está vinculado à mesma OP em outro envio em aberto."

        # 🔹 Não-negativos
        if self.enviado is not None and Decimal(self.enviado) < 0:
            errors["enviado"] = "Enviado deve ser ≥ 0."
        if self.retorno is not None and Decimal(self.retorno) < 0:
            errors["retorno"] = "Retorno deve ser ≥ 0."
        if getattr(self, "sucata", None) is not None and Decimal(self.sucata) < 0:
            errors["sucata"] = "Sucata deve ser ≥ 0."
        if getattr(self, "refugo", None) is not None and Decimal(self.refugo) < 0:
            errors["refugo"] = "Refugo deve ser ≥ 0."


        if errors:
            raise ValidationError(errors)


@receiver(post_save, sender=EstoqueIntermediarioItem)
@receiver(post_delete, sender=EstoqueIntermediarioItem)
def _eiitem_touch_header(sender, instance, **kwargs):
    """Mantém totais do cabeçalho sincronizados ao salvar/excluir itens."""
    try:
        instance.parent.recalc_totais(save=True)
    except Exception:
        # Evita recursões/erros silenciosamente; logs podem ser adicionados se desejar
        pass
