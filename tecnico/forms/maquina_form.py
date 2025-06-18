from django import forms
from tecnico.models.maquina import Maquina

class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = ["codigo", "nome", "servico_realizado", "velocidade", "valor_hora", "consumo_kwh"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Código da máquina"}),
            "nome": forms.TextInput(attrs={"placeholder": "Nome da máquina"}),
            "servico_realizado": forms.TextInput(attrs={"placeholder": "Descrição do serviço"}),
            "velocidade": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Unidades por hora"}),
            "valor_hora": forms.NumberInput(attrs={"step": "0.01", "placeholder": "R$/hora"}),
            "consumo_kwh": forms.NumberInput(attrs={"step": "0.01", "placeholder": "kWh"}),
        }
