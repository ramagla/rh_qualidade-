# qualidade_fornecimento/models/norma.py
from django.db import models


class NormaTecnica(models.Model):
    """
    Cabeçalho da norma técnica.
    Ex.: NBR‑ISO 16120‑1, ASTM A580, etc.
    """

    nome_norma = models.CharField("Nome da Norma", max_length=100)
    arquivo_norma = models.FileField(
        "Arquivo (PDF)", upload_to="normas/", blank=True, null=True
    )
    vinculo_norma = models.CharField(
        "Norma vinculada (tração)", max_length=100, blank=True, null=True
    )

    aprovada = models.BooleanField("Norma aprovada para uso?", default=False)


    class Meta:
        verbose_name = "Norma Técnica"
        verbose_name_plural = "Normas Técnicas"

    def __str__(self):
        return self.nome_norma


class NormaComposicaoElemento(models.Model):
    """
    Cada registro representa UM ‘Tipo de Aço ABNT’
    com os limites mínimo/máximo para os 9 elementos químicos.
    """

    norma = models.ForeignKey(
        NormaTecnica, on_delete=models.CASCADE, related_name="elementos"
    )
    tipo_abnt = models.CharField(
        "Tipo de Aço ABNT", max_length=100, blank=True, null=True
    )

    # ----------  Elementos químicos  ----------
    c_min = models.DecimalField(
        "C mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    c_max = models.DecimalField(
        "C máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    mn_min = models.DecimalField(
        "Mn mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    mn_max = models.DecimalField(
        "Mn máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    si_min = models.DecimalField(
        "Si mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    si_max = models.DecimalField(
        "Si máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    p_min = models.DecimalField(
        "P mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    p_max = models.DecimalField(
        "P máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    s_min = models.DecimalField(
        "S mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    s_max = models.DecimalField(
        "S máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    cr_min = models.DecimalField(
        "Cr mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    cr_max = models.DecimalField(
        "Cr máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    ni_min = models.DecimalField(
        "Ni mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    ni_max = models.DecimalField(
        "Ni máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    cu_min = models.DecimalField(
        "Cu mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    cu_max = models.DecimalField(
        "Cu máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    al_min = models.DecimalField(
        "Al mín (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )
    al_max = models.DecimalField(
        "Al máx (%)", max_digits=5, decimal_places=3, null=True, blank=True
    )

    class Meta:
        verbose_name = "Composição Química (por tipo ABNT)"
        verbose_name_plural = "Composições Químicas"

    def __str__(self):
        return f"ABNT {self.tipo_abnt or '-'} – {self.norma}"


class NormaTracao(models.Model):
    """
    Faixas de resistência à tração para cada norma.
    """

    norma = models.ForeignKey(
        NormaTecnica, on_delete=models.CASCADE, related_name="tracoes"
    )
    tipo_abnt = models.CharField("Tipo ABNT", max_length=100, blank=True, null=True)  # NOVO CAMPO

    bitola_minima = models.DecimalField(
        "Bitola mín (mm)", max_digits=6, decimal_places=2, null=True, blank=True
    )
    bitola_maxima = models.DecimalField(
        "Bitola máx (mm)", max_digits=6, decimal_places=2, null=True, blank=True
    )
    resistencia_min = models.DecimalField(
        "R. tração mín (Kgf/mm²)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    resistencia_max = models.DecimalField(
        "R. tração máx (Kgf/mm²)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    dureza = models.DecimalField(
        "Dureza (HR)", max_digits=6, decimal_places=0, null=True, blank=True
    )

    class Meta:
        verbose_name = "Faixa de Tração"
        verbose_name_plural = "Faixas de Tração"

    def __str__(self):
        return (
            f"{self.norma} – {self.bitola_minima}‑{self.bitola_maxima} mm "
            f"({self.resistencia_min}‑{self.resistencia_max} Kgf/mm²)"
        )


