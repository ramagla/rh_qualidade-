from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from Funcionario.models import Funcionario
from metrologia.models import ControleEntradaSaida, Cota, Dispositivo


class DispositivoForm(forms.ModelForm):
    data_ultima_calibracao = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"
        ),
        input_formats=["%Y-%m-%d"],
        label="Data da Última Calibração",
    )

    class Meta:
        model = Dispositivo
        fields = "__all__"


class ControleEntradaSaidaForm(forms.ModelForm):
    observacao = forms.CharField(
        # Certifique-se de usar o mesmo config_name
        widget=CKEditor5Widget(config_name="default"),
        required=True,
    )

    class Meta:
        model = ControleEntradaSaida
        fields = [
            "tipo_movimentacao",
            "quantidade",
            "colaborador",
            "data_movimentacao",
            "observacao",
            "situacao",
            "setor",
        ]
        widgets = {
            "tipo_movimentacao": forms.Select(attrs={"class": "form-select"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control"}),
            "colaborador": forms.Select(attrs={"class": "form-select"}),
            "data_movimentacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordena os colaboradores por nome
        setores = (
            Funcionario.objects.values_list("local_trabalho", flat=True)
            .distinct()
            .order_by("local_trabalho")
        )
        self.fields["setor"].widget = forms.Select(
            choices=[("", "Selecione um setor")] + [(setor, setor) for setor in setores]
        )

        self.fields["colaborador"].queryset = Funcionario.objects.all().order_by("nome")


class CotaForm(forms.ModelForm):
    class Meta:
        model = Cota
        fields = ["numero", "valor_minimo", "valor_maximo"]
