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
        
    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.title()

    def clean_departamento(self):
        departamento = self.cleaned_data.get('departamento', '')
        return departamento.title()

    def clean_numero_dc(self):
        numero_dc = self.cleaned_data.get('numero_dc', '')
        return numero_dc.strip()  # Apenas como exemplo, caso queira limpar espaços desnecessários

        
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

    def clean_numero_revisao(self):
        numero_revisao = self.cleaned_data.get('numero_revisao', '')
        return numero_revisao.title()

    def clean_descricao_mudanca(self):
        descricao_mudanca = self.cleaned_data.get('descricao_mudanca', '')
        return descricao_mudanca.strip()  # Apenas para remover espaços extras