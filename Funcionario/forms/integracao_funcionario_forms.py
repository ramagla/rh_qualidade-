from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from ..models import Funcionario, IntegracaoFuncionario

class IntegracaoFuncionarioForm(forms.ModelForm):
    """
    Formulário para integração de funcionário.
    Usa CKEditor para treinamentos requeridos e valida que a descrição é obrigatória caso 'Requer Treinamento' seja sim.
    """
    GRUPO_WHATSAPP_CHOICES = [
        (True, "Sim"),
        (False, "Não"),
    ]
    REQUER_TREINAMENTO_CHOICES = [
        (True, "Sim"),
        (False, "Não"),
    ]

    grupo_whatsapp = forms.ChoiceField(
        choices=GRUPO_WHATSAPP_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial=False,
        label="Grupo WhatsApp",
    )
    requer_treinamento = forms.ChoiceField(
        choices=REQUER_TREINAMENTO_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial=False,
        label="Requer Treinamento",
    )
    treinamentos_requeridos = forms.CharField(
        widget=CKEditor5Widget(),
        required=False,
        label="Treinamentos Requeridos"
    )

    class Meta:
        model = IntegracaoFuncionario
        fields = [
            "funcionario",
            "grupo_whatsapp",
            "requer_treinamento",
            "treinamentos_requeridos",
            "data_integracao",
            "pdf_integracao",
        ]
        widgets = {
            "data_integracao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar funcionários ativos e ordenar por nome
        self.fields["funcionario"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")

    def clean(self):
        cleaned_data = super().clean()
        requer_treinamento = cleaned_data.get("requer_treinamento")
        treinamentos_requeridos = cleaned_data.get("treinamentos_requeridos", "").strip()

        # Lógica: se requer_treinamento for "True", campo treinamentos_requeridos é obrigatório
        if str(requer_treinamento) == "True" and not treinamentos_requeridos:
            self.add_error("treinamentos_requeridos", "Descreva os treinamentos requeridos para este funcionário.")
        return cleaned_data
