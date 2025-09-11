# qualidade_fornecimento/models/estoque_intermediario.py — PARA
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

User = get_user_model()


def _q(val: Optional[Decimal]) -> Decimal:
    """Quantiza Decimal para 3 casas (kg) com HALF_UP; trata None como 0."""
    if val is None:
        val = Decimal("0")
    return (Decimal(val) if isinstance(val, Decimal) else Decimal(str(val))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


class EstoqueIntermediario(models.Model):
    STATUS = [
        ("EM_FABRICA", "Em Fábrica"),
        ("RETORNADO", "Retornado"),
        ("CANCELADO", "Cancelado"),
    ]
    TURNO_CHOICES = [("A", "A"), ("B", "B"), ("C", "C")]

    # Identificação / vínculos
    op = models.CharField("OP", max_length=30, db_index=True)
    materia_prima = models.ForeignKey(
        "qualidade_fornecimento.MateriaPrimaCatalogo",
        on_delete=models.PROTECT,
        related_name="estoques_intermediarios",
        verbose_name="Matéria-prima",
    )
    lote = models.ForeignKey(
        "qualidade_fornecimento.RoloMateriaPrima",
        on_delete=models.PROTECT,
        related_name="itens_estoque_intermediario",
        verbose_name="Lote / Rolo",
    )
    tb050 = models.ForeignKey(
        "qualidade_fornecimento.RelacaoMateriaPrima",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="itens_estoque_intermediario",
        verbose_name="TB050 (opcional)",
    )

    # Planejado (para consumo por peça)
    qtde_op_prevista = models.DecimalField("Qtd MP prevista (kg)", max_digits=12, decimal_places=3)
    pecas_planejadas_op = models.PositiveIntegerField("Peças planejadas OP")

    # Movimentações / apontamentos
    enviado = models.DecimalField("Enviado à fábrica (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    retorno = models.DecimalField("Retorno (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    sucata = models.DecimalField("Sucata (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    refugo = models.DecimalField("Refugo (kg)", max_digits=12, decimal_places=3, default=Decimal("0.000"))
    pecas_apontadas = models.PositiveIntegerField("Peças apontadas", default=0)

    # Cálculos (persistidos para auditoria)
    consumo_inferido_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    consumo_balanca_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    consumo_real_kg = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))

    # Configuração e controle
    tolerancia_sucata_percentual = models.DecimalField("Tolerância de sucata (%)", max_digits=5, decimal_places=2, default=Decimal("3.00"))
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

    setor = models.CharField(max_length=60, blank=True)
    linha = models.CharField(max_length=60, blank=True)
    maquina = models.ForeignKey("tecnico.Maquina", on_delete=models.SET_NULL, null=True, blank=True)
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES, blank=True)

    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="estoque_intermediario/%Y/%m/", blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ei_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ei_updated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    justificativa_excesso = models.TextField("Justificativa p/ excesso de sucata", blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["op", "lote"],
                condition=Q(status="EM_FABRICA"),
                name="uniq_ei_op_lote_em_fabrica",
            )
        ]
        permissions = [
            ("close_estoqueintermediario", "Pode fechar item do Estoque Intermediário"),
            ("export_estoqueintermediario", "Pode exportar Estoque Intermediário"),
        ]

    # --------- Propriedades / KPIs ---------
    @property
    def consumo_por_peca_planejado(self) -> Decimal:
        if not self.pecas_planejadas_op:
            return Decimal("0.000")
        return _q(self.qtde_op_prevista) / Decimal(self.pecas_planejadas_op)

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

        # 2) consumo balança
        cb = _q(_q(self.enviado) - _q(self.retorno))
        if cb < 0:
            cb = Decimal("0.000")

        # 3) real
        cr = ci if ci >= cb else cb

        self.consumo_inferido_kg = ci
        self.consumo_balanca_kg = cb
        self.consumo_real_kg = cr

    def clean(self):
        # Amarra TB050 com Lote/MP se faltar
        if self.lote and not self.tb050:
            self.tb050 = getattr(self.lote, "tb050", None)

        if self.materia_prima and self.tb050:
            mp_tb = getattr(self.tb050, "materia_prima_id", None)
            if mp_tb and mp_tb != self.materia_prima_id:
                raise ValidationError({"tb050": "TB050 não corresponde à Matéria-prima selecionada."})

        if self.pecas_planejadas_op <= 0:
            raise ValidationError({"pecas_planejadas_op": "Peças planejadas deve ser > 0."})

        self._atualizar_calculos()

        if self.status == "RETORNADO":
            # Se retornado, validar sucata vs tolerância
            tol = (self.tolerancia_sucata_percentual or Decimal("3.00")).quantize(Decimal("0.01"))
            if self.perc_sucata > tol and not self.justificativa_excesso:
                raise ValidationError({"justificativa_excesso": f"Percentual de sucata {self.perc_sucata}% excede tolerância {tol}%. Informe justificativa."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OP {self.op} • {self.materia_prima} • Lote {self.lote_id or '-'}"