from django import forms
from ..models import Evento

class EventoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de Eventos.
    Usa widgets do tipo date para datas e valida que a data de fim não antecede a data de início.
    """

    data_inicio = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
        label="Data de Início",
    )

    data_fim = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
        label="Data de Fim",
    )

    class Meta:
        model = Evento
        fields = ["titulo", "descricao", "data_inicio", "data_fim", "cor", "tipo"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cor": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        """
        Garante que a data de fim não seja anterior à data de início.
        """
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError(
                "A data de fim não pode ser anterior à data de início."
            )
        return cleaned_data
