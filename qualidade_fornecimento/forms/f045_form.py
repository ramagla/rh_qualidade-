# qualidade_fornecimento/forms/f045_form.py
from django import forms
from ..models.f045 import RelatorioF045
from qualidade_fornecimento.utils import extrair_bitola      # já existe
from decimal import Decimal

class RelatorioF045Form(forms.ModelForm):
    class Meta:
        model  = RelatorioF045
        exclude = ("relacao", "laudo_composicao", "laudo_final",
                   "assinado_por", "assinado_email", "pdf",
                   "nro_relatorio", "fornecedor", "nota_fiscal",
                   "numero_certificado", "material", "bitola",
                   "qtd_rolos", "massa_liquida")

        widgets = {
            "pedido_compra": forms.TextInput(attrs={"class": "form-control"}),
            # demais campos manuais → TextInput / NumberInput
        }

    def clean(self):
        data = super().clean()
        # --- regra de cor / laudo ---------------------------
        limites = self.initial.get("limites_quimicos", {})   # virá da view
        laudo = "Aprovado"
        for campo, (vmin, vmax) in limites.items():
            valor = data.get(f"{campo}_user")
            if valor is None:
                laudo = "Reprovado"
                continue
            if not (Decimal(vmin) <= valor <= Decimal(vmax)):
                laudo = "Reprovado"
        self.instance.laudo_composicao = laudo
        return data
