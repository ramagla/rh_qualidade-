from decimal import Decimal, InvalidOperation

from django.db import models

from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima


class RoloMateriaPrima(models.Model):
    tb050 = models.ForeignKey(
        RelacaoMateriaPrima, related_name="rolos", on_delete=models.CASCADE
    )
    nro_rolo = models.CharField("N° do Rolo", max_length=50, blank=True)
    peso = models.DecimalField(
        "Peso", max_digits=10, decimal_places=2, blank=True, null=True
    )

    # Campos de inspeção individual
    tracao = models.DecimalField(
        "Resistência à Tração", max_digits=6, decimal_places=2, null=True, blank=True
    )
    dureza = models.DecimalField(
        "Dureza", max_digits=6, decimal_places=2, null=True, blank=True
    )

    bitola_espessura = models.DecimalField(
        "Espessura", max_digits=6, decimal_places=2, null=True, blank=True
    )
    bitola_largura = models.DecimalField(
        "Largura", max_digits=6, decimal_places=2, null=True, blank=True
    )

    enrolamento = models.CharField(
        max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )
    dobramento = models.CharField(
        max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )
    torcao_residual = models.CharField(
        max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )
    aspecto_visual = models.CharField(
        max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )
    alongamento = models.CharField(
        "Alongamento", max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )  # <<< novo campo
    flechamento = models.CharField(
        "Flechamento", max_length=10, choices=[("OK", "OK"), ("NOK", "NOK")], blank=True
    )  # <<< novo campo

    laudo = models.CharField(max_length=20, default="Aguardando")

    def aprova_rolo(
        self, bitola, largura, tol_esp, tol_larg, res_min, res_max, dureza_lim
    ):
        try:
            bitola = Decimal(str(bitola).replace(",", ".")) if bitola is not None else None
            tol_esp = Decimal(str(tol_esp).replace(",", ".")) if tol_esp is not None else None
            largura = Decimal(str(largura).replace(",", ".")) if largura is not None else None
            tol_larg = Decimal(str(tol_larg).replace(",", ".")) if tol_larg is not None else None
            res_min = Decimal(str(res_min).replace(",", ".")) if res_min is not None else None
            res_max = Decimal(str(res_max).replace(",", ".")) if res_max is not None else None
            dureza_lim = Decimal(str(dureza_lim).replace(",", ".")) if dureza_lim is not None else None
        except (InvalidOperation, TypeError):
            self.laudo = "Reprovado"
            return self.laudo

        esp_ok = (
            self.bitola_espessura is not None
            and bitola is not None
            and tol_esp is not None
            and (bitola - tol_esp) <= self.bitola_espessura <= (bitola + tol_esp)
        )

        larg_ok = (
            self.bitola_largura is not None
            and largura is not None
            and tol_larg is not None
            and (largura - tol_larg) <= self.bitola_largura <= (largura + tol_larg)
        )

        tracao_ok = (
            self.tracao is not None
            and res_min is not None
            and res_max is not None
            and res_min <= self.tracao <= res_max
        )

        dureza_ok = self.dureza is None or (
            dureza_lim is not None and self.dureza <= dureza_lim
        )

        extras_ok = all(
            [
                self.enrolamento == "OK",
                self.dobramento == "OK",
                self.torcao_residual == "OK",
                self.aspecto_visual == "OK",
                self.alongamento == "OK",
                self.flechamento == "OK",
            ]
        )

        aprovado = esp_ok and larg_ok and tracao_ok and dureza_ok and extras_ok
        self.laudo = "Aprovado" if aprovado else "Reprovado"
        return self.laudo

    def save(self, *args, **kwargs):
        if not self.nro_rolo:
            ultimo = RoloMateriaPrima.objects.order_by("-id").first()
            ultimo_numero = (
                int(ultimo.nro_rolo) if ultimo and ultimo.nro_rolo.isdigit() else 49999
            )
            self.nro_rolo = str(ultimo_numero + 1)
        super().save(*args, **kwargs)
