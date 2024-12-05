from django import forms
from ..models import Funcionario, Cargo
from django_select2.forms import Select2Widget


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

    cargo_inicial = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        label="Cargo Inicial",
        widget=Select2Widget(attrs={'class': 'select2 form-select', 'id': 'id_cargo_inicial'})
    )
    cargo_atual = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        label="Cargo Atual",
        widget=Select2Widget(attrs={'class': 'select2 form-select', 'id': 'id_cargo_atual'})
    )
    data_admissao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Data de Admissão")
    data_integracao = forms.DateField(
    required=False,  # Torna o campo opcional
    widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    label="Data de Integração"
)
    escolaridade = forms.ChoiceField(choices=ESCOLARIDADE_CHOICES, label="Escolaridade", widget=forms.Select(attrs={'class': 'form-select'}))
    responsavel = forms.ModelChoiceField(
            queryset=Funcionario.objects.all(),
            required=False,
            widget=Select2Widget(attrs={'class': 'select2 form-select','id': 'id_responsavel'})
        )    
    foto = forms.ImageField(required=False, label="Foto")
    curriculo = forms.FileField(required=False, label="Currículo")
    status = forms.ChoiceField(choices=Funcionario.STATUS_CHOICES, label="Status", widget=forms.Select(attrs={'class': 'form-select'}))
    formulario_f146 = forms.FileField(required=False, label="Formulário F146")
    
    # Novo campo Experiência Profissional
    experiencia_profissional = forms.ChoiceField(
        choices=Funcionario.EXPERIENCIA_CHOICES, 
        label="Experiência Profissional", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Funcionario
        fields = [
            'nome', 'data_admissao', 'cargo_inicial', 'cargo_atual', 'numero_registro', 
            'local_trabalho', 'data_integracao', 'escolaridade', 'responsavel', 'foto', 
            'curriculo', 'status', 'formulario_f146', 'experiencia_profissional'  # Inclua o novo campo aqui
        ]

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if not isinstance(self.fields[field].widget, Select2Widget):  # Evita sobrescrever widgets Select2
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    # Métodos para limpar e formatar os campos
    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.title()  # Converte para Title Case

    def clean_local_trabalho(self):
        local_trabalho = self.cleaned_data.get('local_trabalho', '')
        return local_trabalho.title()  # Converte para Title Case

    def clean_responsavel(self):
        responsavel = self.cleaned_data.get('responsavel', None)
        if responsavel:
            responsavel.nome = responsavel.nome.title()  # Converte para Title Case
        return responsavel