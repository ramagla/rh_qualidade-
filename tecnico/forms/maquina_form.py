from django import forms
from tecnico.models.maquina import Maquina, ServicoRealizado

class MaquinaForm(forms.ModelForm):
    turma_choices = [(k, v) for k, v in Maquina.FAMILIA_PRODUTO_LABELS.items()]

    grupo_de_maquinas = forms.ChoiceField(
        choices=turma_choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Grupo de Máquinas"
    )

    servicos_realizados = forms.ModelMultipleChoiceField(
        queryset=ServicoRealizado.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-select select2"}),
        required=False,
        label="Serviços Realizados"
    )

    class Meta:
        model = Maquina
        fields = [
            "codigo", "nome", "grupo_de_maquinas",
            "servicos_realizados", "velocidade",
            "valor_hora", "consumo_kwh"
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Código da máquina"}),
            "nome": forms.TextInput(attrs={"placeholder": "Nome da máquina"}),
            "velocidade": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Unidades por hora"}),
            "valor_hora": forms.NumberInput(attrs={"step": "0.01", "placeholder": "R$/hora"}),
            "consumo_kwh": forms.NumberInput(attrs={"step": "0.01", "placeholder": "kWh"}),
        }
