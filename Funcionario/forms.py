from django import forms
from .models import Funcionario, Cargo, Revisao, Treinamento,ListaPresenca

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
    responsavel = forms.ModelChoiceField(queryset=Funcionario.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    foto = forms.ImageField(required=False, label="Foto")  # Novo campo para foto
    curriculo = forms.FileField(required=False, label="Currículo")  # Novo campo para currículo

    class Meta:
        model = Funcionario
        fields = ['nome', 'data_admissao', 'cargo_inicial', 'cargo_atual', 'numero_registro', 'local_trabalho', 'data_integracao', 'escolaridade', 'responsavel', 'foto', 'curriculo']  # Inclua os novos campos

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields['responsavel'].queryset = Funcionario.objects.all()

            self.fields[field].widget.attrs.update({'class': 'form-control'})

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome', 'cbo', 'descricao_arquivo', 'departamento']  # Adiciona o campo 'departamento'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cbo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),  # Widget para 'departamento'
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

class TreinamentoForm(forms.ModelForm):
    class Meta:
        model = Treinamento
        fields = ['funcionario', 'tipo', 'categoria', 'nome_curso', 'instituicao_ensino', 'status', 'data_inicio', 'data_fim', 'carga_horaria', 'anexo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(choices=Treinamento.TIPO_TREINAMENTO_CHOICES, attrs={'class': 'form-select'}),
            'categoria': forms.Select(choices=Treinamento.CATEGORIA_CHOICES, attrs={'class': 'form-select'}),
            'nome_curso': forms.TextInput(attrs={'class': 'form-control'}),
            'instituicao_ensino': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(choices=Treinamento.STATUS_CHOICES, attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'carga_horaria': forms.TextInput(attrs={'class': 'form-control'}),
            'anexo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ListaPresencaForm(forms.ModelForm):
    class Meta:
        model = ListaPresenca
        fields = ['treinamento', 'data_realizacao', 'horario_inicio', 'horario_fim', 'instrutor', 'duracao', 'necessita_avaliacao', 'lista_presenca', 'participantes', 'assunto', 'descricao']
        widgets = {
            'participantes': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duracao': forms.TextInput(attrs={'class': 'form-control'}),
            'instrutor': forms.TextInput(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),  # Novo campo
            'descricao': forms.Textarea(attrs={'class': 'form-control'}),  # Novo campo
        }
