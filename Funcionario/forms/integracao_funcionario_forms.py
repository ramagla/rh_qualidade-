from django import forms
from ..models import IntegracaoFuncionario
from django_ckeditor_5.widgets import CKEditor5Widget

class IntegracaoFuncionarioForm(forms.ModelForm):
    treinamentos_requeridos = forms.CharField(widget=CKEditor5Widget(), required=False)

    GRUPO_WHATSAPP_CHOICES = [
        (True, 'Sim'),
        (False, 'Não'),
    ]
    REQUER_TREINAMENTO_CHOICES = [
        (True, 'Sim'),
        (False, 'Não'),
    ]

    grupo_whatsapp = forms.ChoiceField(
        choices=GRUPO_WHATSAPP_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False,
        label="Grupo WhatsApp"
    )
    requer_treinamento = forms.ChoiceField(
        choices=REQUER_TREINAMENTO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False,
        label="Requer Treinamento"
    )

    treinamentos_requeridos = forms.CharField(
        widget=CKEditor5Widget(),
        required=False
    )

    class Meta:
        model = IntegracaoFuncionario
        fields = ['funcionario', 'grupo_whatsapp', 'requer_treinamento', 'treinamentos_requeridos', 'data_integracao', 'pdf_integracao']
        widgets = {
            'data_integracao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }

    def clean_funcionario(self):
        funcionario = self.cleaned_data.get('funcionario')
        if funcionario:
            return funcionario.title()
        return funcionario