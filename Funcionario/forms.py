from django import forms
from .models import Funcionario, Cargo, Revisao

class FuncionarioForm(forms.ModelForm):
    ESCOLARIDADE_CHOICES = [
        ('Fundamental Incompleto', 'Fundamental Incompleto'),
        ('Fundamental Completo', 'Fundamental Completo'),
        ('Médio Incompleto', 'Médio Incompleto'),
        ('Médio Completo', 'Médio Completo'),
        ('Superior Incompleto', 'Superior Incompleto'),
        ('Superior Completo', 'Superior Completo'),
        ('Pós-graduação', 'Pós-graduação'),
        ('Mestrado', 'Mestrado'),
        ('Doutorado', 'Doutorado'),
    ]
    
    cargo_inicial = forms.ModelChoiceField(queryset=Cargo.objects.all(), label="Cargo Inicial", widget=forms.Select(attrs={'class': 'form-select'}))
    cargo_atual = forms.ModelChoiceField(queryset=Cargo.objects.all(), label="Cargo Atual", widget=forms.Select(attrs={'class': 'form-select'}))
    data_admissao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Data de Admissão")
    data_integracao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Data de Integração")
    escolaridade = forms.ChoiceField(choices=ESCOLARIDADE_CHOICES, label="Escolaridade", widget=forms.Select(attrs={'class': 'form-select'}))
    
    responsavel = forms.ModelChoiceField(queryset=Funcionario.objects.all(), label="Responsável", required=False, widget=forms.Select(attrs={'class': 'form-select'}))


    class Meta:
        model = Funcionario
        fields = ['nome', 'data_admissao', 'cargo_inicial', 'cargo_atual', 'numero_registro', 'local_trabalho', 'data_integracao', 'escolaridade', 'responsavel']

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome', 'cbo', 'descricao_arquivo', 'numero_revisao', 'data_ultima_atualizacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cbo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'numero_revisao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_ultima_atualizacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class RevisaoForm(forms.ModelForm):
    class Meta:
        model = Revisao
        fields = ['numero_revisao', 'data_revisao', 'descricao_mudanca']
        widgets = {
            'numero_revisao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_revisao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao_mudanca': forms.Textarea(attrs={'class': 'form-control'}),
        }