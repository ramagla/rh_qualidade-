from django import forms
from Funcionario.models import AtualizacaoSistema
from django_ckeditor_5.widgets import CKEditor5Widget

class AtualizacaoSistemaForm(forms.ModelForm):

    class Meta:
        model = AtualizacaoSistema
        fields = [
            'titulo',
            'descricao',
            'previa_versao',
            'previsao',
            'versao',
            'status',
            'data_termino',
            'arquivo_pdf'  # <<< Adicionado para upload manual
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'versao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1.6.5'}),
            'previsao': forms.DateInput(format="%Y-%m-%d", attrs={'class': 'form-control', 'type': 'date'}),
            'data_termino': forms.DateInput(format="%Y-%m-%d", attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'previa_versao': CKEditor5Widget(config_name="default", attrs={"placeholder": "Digite a prévia da versão"}),
            'descricao': CKEditor5Widget(config_name="default", attrs={"placeholder": "Digite a descrição da atualização"}),
            'arquivo_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),  # <<< Adicionado
        }
