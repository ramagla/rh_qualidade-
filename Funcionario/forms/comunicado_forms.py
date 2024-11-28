from django import forms
from ..models import Comunicado
from django_ckeditor_5.widgets import CKEditor5Widget

class ComunicadoForm(forms.ModelForm):
    descricao = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),  # Certifique-se de usar o mesmo config_name
        required=True
    )
 
    class Meta:
        model = Comunicado
        fields = ['data', 'assunto', 'descricao', 'tipo', 'departamento_responsavel', 'lista_assinaturas']

        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),           
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'departamento_responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'lista_assinaturas': forms.FileInput(attrs={'class': 'form-control'}),

        }