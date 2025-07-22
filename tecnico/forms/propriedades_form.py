from django import forms
from tecnico.models.roteiro import PropriedadesEtapa

class PropriedadesEtapaForm(forms.ModelForm):
    class Meta:
        model = PropriedadesEtapa
        fields = [
            "nome_acao", "descricao_detalhada", "maquinas", "ferramenta",
            "seguranca_mp", "seguranca_ts", "seguranca_m1", "seguranca_l1", "seguranca_l2"  # 👈 novos
        ]      
        widgets = {
            "nome_acao": forms.TextInput(attrs={"class": "form-control"}),
            "descricao_detalhada": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "maquinas": forms.SelectMultiple(attrs={"class": "form-select select2"}),
            "ferramenta": forms.Select(attrs={"class": "form-select select2"}),

            # novos widgets tipo switch (se quiser usar estilo bootstrap-switch)
            "seguranca_mp": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_ts": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_m1": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_l1": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_l2": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
