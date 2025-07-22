from django import forms
from tecnico.models.maquina import Maquina

from tecnico.models.maquina import Maquina, ServicoRealizado

class MaquinaForm(forms.ModelForm):
    servicos_realizados = forms.ModelMultipleChoiceField(
        queryset=ServicoRealizado.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-select select2"}),
        required=False,
        label="Serviços Realizados"
    )

    class Meta:
        model = Maquina
        fields = ["codigo", "nome", "servicos_realizados", "velocidade", "valor_hora", "consumo_kwh"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Código da máquina"}),
            "nome": forms.TextInput(attrs={"placeholder": "Nome da máquina"}),
            "velocidade": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Unidades por hora"}),
            "valor_hora": forms.NumberInput(attrs={"step": "0.01", "placeholder": "R$/hora"}),
            "consumo_kwh": forms.NumberInput(attrs={"step": "0.01", "placeholder": "kWh"}),
        }
