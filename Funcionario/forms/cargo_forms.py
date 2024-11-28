from django import forms
from ..models import Cargo, Revisao
from django_ckeditor_5.widgets import CKEditor5Widget

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome', 'numero_dc', 'descricao_arquivo', 'departamento']  # Campo 'numero_dc' no lugar de 'cbo'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_dc': forms.TextInput(attrs={'class': 'form-control'}),  # Atualizado para 'numero_dc'
            'descricao_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),  # Widget para 'departamento'
        }
        
class RevisaoForm(forms.ModelForm):
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    class Meta:
        model = Revisao
        fields = ['numero_revisao', 'data_revisao', 'descricao_mudanca']
        widgets = {
            'numero_revisao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_revisao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # 'descricao_mudanca': forms.Textarea(attrs={'class': 'form-control'}),
        }