from django import forms

from ..models.models_tabelatecnica import TabelaTecnica


class TabelaTecnicaForm(forms.ModelForm):
    class Meta:
        model = TabelaTecnica
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(TabelaTecnicaForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

        # Configuração específica para o campo de data
        self.fields["data_ultima_calibracao"].widget = forms.DateInput(
            attrs={
                "type": "date",  # Ativa o seletor de data
                "class": "form-control",  # Aplica estilo Bootstrap
            },
            format="%Y-%m-%d",  # Define o formato de exibição e entrada
        )

    def clean_data_ultima_calibracao(self):
        data = self.cleaned_data["data_ultima_calibracao"]
        # Validações adicionais, se necessário
        return data
