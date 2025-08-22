from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import models

from qualidade_fornecimento.models.norma import NormaTecnica, NormaTracao

from .materiaPrima import RelacaoMateriaPrima

User = get_user_model()


class RelatorioF045(models.Model):
    """
    Relatório F‑045 – Inspeção de Material
    """

    # ❶ Dados automáticos (copiados da relação no momento da criação)
    relacao = models.OneToOneField(
        RelacaoMateriaPrima, on_delete=models.CASCADE, related_name="f045"
    )
    nro_relatorio = models.PositiveIntegerField(editable=False)
    fornecedor = models.CharField(max_length=120, editable=False)
    nota_fiscal = models.CharField(max_length=50, editable=False)
    numero_certificado = models.CharField(max_length=50, editable=False)
    material = models.CharField(max_length=200, editable=False)
    bitola = models.CharField(max_length=30, editable=True)
    qtd_rolos = models.PositiveIntegerField(editable=False)
    massa_liquida = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    # ❷ Campos de inserção manual (cabeçalho)
    qtd_carreteis = models.PositiveIntegerField(null=True, blank=True)
    pedido_compra = models.CharField(max_length=50, null=True, blank=True)

    # ❸ Resultados da composição química
    c_user = models.DecimalField(
        "C (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    mn_user = models.DecimalField(
        "Mn (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    si_user = models.DecimalField(
        "Si (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    p_user = models.DecimalField(
        "P (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    s_user = models.DecimalField(
        "S (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    cr_user = models.DecimalField(
        "Cr (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    ni_user = models.DecimalField(
        "Ni (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    cu_user = models.DecimalField(
        "Cu (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )
    al_user = models.DecimalField(
        "Al (%)", max_digits=7, decimal_places=4, null=True, blank=True
    )

    laudo_composicao = models.CharField(
        "Laudo – composição",
        max_length=2,
        choices=[("Ap", "Aprovado"), ("Re", "Reprovado")],
        editable=False,
        blank=True,
    )

    # ❹ Laudo interno consolidado (com base nos rolos)
    laudo_interno = models.CharField(
        "Laudo – características internas",
        max_length=2,
        choices=[("Ap", "Aprovado"), ("Re", "Reprovado")],
        editable=False,
        blank=True,
    )

    observacoes = models.TextField(max_length=1200, null=True, blank=True)

    # ❺ Outras características do certificado do fornecedor
    resistencia_tracao = models.CharField(
        max_length=50, default="N/A", null=True, blank=True
    )
    escoamento = models.CharField(max_length=50, default="N/A", null=True, blank=True)
    alongamento = models.CharField(max_length=50, default="N/A", null=True, blank=True)
    estriccao = models.CharField(max_length=50, default="N/A", null=True, blank=True)
    torcao_certificado = models.CharField(
        max_length=50, default="N/A", null=True, blank=True
    )
    dureza_certificado = models.CharField(
        "Dureza (certificado)", max_length=50, default="N/A", null=True, blank=True
    )

    status_geral = models.CharField(max_length=30, blank=True, editable=False)

   # Metadados
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)


    class Meta:
        verbose_name = "Relatório F‑045"
        verbose_name_plural = "Relatórios F‑045"

    def __str__(self):
        return f"F045 – Relatório {self.nro_relatorio}"

    # ❼ Regras automáticas de laudo
    def avaliar_composicao(self, limites: dict[str, tuple[Decimal, Decimal]]):
        for sigla, (vmin, vmax) in limites.items():
            valor = getattr(self, f"{sigla}_user")

            # Se intervalo não definido → ignora (considera aprovado)
            if vmin is None or vmax is None:
                continue

            # Se intervalo for 0–0 → ignora (considera aprovado)
            if vmin == 0 and vmax == 0:
                continue

            if valor is None:
                return "Re"

            if not (vmin <= valor <= vmax):
                return "Re"

        return "Ap"


    def avaliar_interno(self):
        rolos = self.relacao.rolos.all()
        if not rolos.exists():
            return "Re"

        # Obtém limites da norma aplicáveis à bitola do cadastro
        try:
            norma = NormaTecnica.objects.get(
                nome_norma=self.relacao.materia_prima.norma
            )
            bitola_str = str(self.relacao.materia_prima.bitola).replace(",", ".")
            bitola_val = float(bitola_str)

            tracao = NormaTracao.objects.filter(
                norma=norma,
                bitola_minima__lte=bitola_val,
                bitola_maxima__gte=bitola_val,
            ).first()
            res_min = Decimal(str(tracao.resistencia_min)) if tracao and tracao.resistencia_min is not None else None
            res_max = Decimal(str(tracao.resistencia_max)) if tracao and tracao.resistencia_max is not None else None
            dureza_limite = (
                Decimal(str(tracao.dureza).replace(",", "."))
                if tracao and tracao.dureza
                else None
            )
        except Exception:
            res_min = None
            res_max = None
            dureza_limite = None

        # 1) Regras por rolo (mantidas)
        for rolo in rolos:
            if dureza_limite is not None and rolo.dureza is not None:
                if rolo.dureza > dureza_limite:
                    return "Re"

            for campo in [
                "enrolamento",
                "dobramento",
                "torcao_residual",
                "aspecto_visual",
            ]:
                if getattr(rolo, campo, "").upper() != "OK":
                    return "Re"

        # 2) Regras pelos campos do certificado do fornecedor (novas)
        #    - Tração do certificado fora de [res_min, res_max] => Re
        #    - Dureza do certificado acima do limite da norma  => Re
        def _parse_decimal_str(valor):
            if valor is None:
                return None
            s = str(valor).strip()
            s = s.replace("kgf/mm2", "").replace("kgf/mm²", "").replace("MPa", "").replace("HRB", "").replace("HRC", "")
            s = s.replace(",", ".")
            try:
                return Decimal(s)
            except Exception:
                return None

        tracao_cert = _parse_decimal_str(self.resistencia_tracao)
        dureza_cert = _parse_decimal_str(self.dureza_certificado)

        if tracao is not None and tracao_cert is not None and res_min is not None and res_max is not None:
            if not (res_min <= tracao_cert <= res_max):
                return "Re"

        if dureza_limite is not None and dureza_cert is not None:
            if dureza_cert > dureza_limite:
                return "Re"

        return "Ap"


    def save(self, *args, **kwargs):
        limites = kwargs.pop("limites_quimicos", None)
        aprovado_manual = kwargs.pop("aprovado_manual", False)

        # Sempre recalcula o laudo interno (baseado nos rolos)
        self.laudo_interno = self.avaliar_interno()

        # Se limites químicos foram enviados, avalia a composição
        if limites is not None:
            self.laudo_composicao = self.avaliar_composicao(limites)

        # Agora define o status geral:
        if aprovado_manual:
            self.status_geral = "Aprovado Condicionalmente"
        elif self.laudo_composicao == "Ap" and self.laudo_interno == "Ap":
            self.status_geral = "Aprovado"
        else:
            self.status_geral = "Reprovado"

        super().save(*args, **kwargs)
