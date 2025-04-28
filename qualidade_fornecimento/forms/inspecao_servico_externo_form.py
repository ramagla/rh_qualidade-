from django import forms

from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)


class InspecaoServicoExternoForm(forms.ModelForm):
    class Meta:
        model = InspecaoServicoExterno
        exclude = ["servico"]  # <==== Aqui! Exclui o campo servico

        fields = "__all__"
