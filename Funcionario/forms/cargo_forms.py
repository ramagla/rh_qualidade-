from django import forms
from ..models import Cargo, Revisao, Funcionario
from django_ckeditor_5.widgets import CKEditor5Widget
from django_select2.forms import Select2Widget


class CargoForm(forms.ModelForm):
    # Definindo os campos com CKEditor5Widget
    responsabilidade_atividade_primaria = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )
    responsabilidade_atividade_secundaria = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )
    educacao_minima = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )
    treinamento_externo = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )
    treinamento_interno_minimo = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )
    experiencia_minima = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),
        required=True
    )

    class Meta:
        model = Cargo
        fields = [
            'nome', 
            'numero_dc', 
            'descricao_arquivo', 
            'departamento', 
            'responsabilidade_atividade_primaria', 
            'responsabilidade_atividade_secundaria', 
            'educacao_minima', 
            'treinamento_externo', 
            'treinamento_interno_minimo', 
            'experiencia_minima',  # VÍRGULA ADICIONADA AQUI
            'elaborador',
            'elaborador_data',
            'aprovador',
            'aprovador_data'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_dc': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'elaborador': forms.Select(attrs={'class': 'form-control'}),
            'elaborador_data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'aprovador': forms.Select(attrs={'class': 'form-control'}),
            'aprovador_data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar funcionários ativos e ordenar alfabeticamente
        self.fields['elaborador'].queryset = Funcionario.objects.filter(
            status='Ativo'
        ).order_by('nome')
        self.fields['aprovador'].queryset = Funcionario.objects.filter(
            status='Ativo'
        ).order_by('nome')   
        
    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.title()

    def clean_departamento(self):
        departamento = self.cleaned_data.get('departamento', '')
        return departamento.title()

    def clean_numero_dc(self):
        numero_dc = self.cleaned_data.get('numero_dc', '')
        return numero_dc.strip()  # Apenas exemplo para limpar espaços desnecessários

        
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