from django import forms
from portaria.models.ligacao import LigacaoPortaria

class LigacaoPortariaForm(forms.ModelForm):
    class Meta:
        model = LigacaoPortaria
        fields = ["nome", "numero", "empresa", "falar_com", "data", "horario", "recado"]
        widgets = {
            "data": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
            "recado": forms.Textarea(attrs={"rows": 3}),
        }
