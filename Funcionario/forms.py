from django import forms
from .models import Funcionario, Cargo, Revisao, Treinamento,ListaPresenca,AvaliacaoTreinamento,AvaliacaoDesempenho,JobRotationEvaluation
from django_ckeditor_5.widgets import CKEditor5Widget

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
            self.fields[field].widget.attrs.update({'class': 'form-control'})


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
        fields = '__all__'
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
    descricao = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = ListaPresenca
        fields = [
            'treinamento', 'data_realizacao', 'horario_inicio', 'horario_fim', 
            'instrutor', 'duracao', 'necessita_avaliacao', 'lista_presenca', 
            'participantes', 'assunto', 'descricao'
        ]
        widgets = {
            'data_realizacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'participantes': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duracao': forms.TextInput(attrs={'class': 'form-control'}),
            'instrutor': forms.TextInput(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoTreinamento
        fields = ['funcionario', 'treinamento', 'data_avaliacao', 'responsavel_1_nome', 'responsavel_1_cargo', 
                  'responsavel_2_nome', 'responsavel_2_cargo', 'responsavel_3_nome', 'responsavel_3_cargo', 
                  'pergunta_1', 'pergunta_2', 'pergunta_3', 'descricao_melhorias', 'avaliacao_geral']


from django import forms
from .models import AvaliacaoTreinamento, Funcionario, ListaPresenca

class AvaliacaoTreinamentoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoTreinamento
        fields = '__all__'

        # Adicionando classes diretamente aos widgets
        widgets = {
            'responsavel_1_nome': forms.Select(attrs={'class': 'responsavel-nome'}),
            'responsavel_1_cargo': forms.TextInput(attrs={'class': 'responsavel-cargo', 'readonly': 'readonly'}),
            'responsavel_2_nome': forms.Select(attrs={'class': 'responsavel-nome'}),
            'responsavel_2_cargo': forms.TextInput(attrs={'class': 'responsavel-cargo', 'readonly': 'readonly'}),
            'responsavel_3_nome': forms.Select(attrs={'class': 'responsavel-nome'}),
            'responsavel_3_cargo': forms.TextInput(attrs={'class': 'responsavel-cargo', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super(AvaliacaoTreinamentoForm, self).__init__(*args, **kwargs)

        # Alterando o campo treinamento para pegar da ListaPresenca
        self.fields['treinamento'].queryset = ListaPresenca.objects.all()
        self.fields['treinamento'].label = 'Treinamento/Curso'

        # Preenchendo o campo de responsáveis com os funcionários (Select)
        self.fields['responsavel_1_nome'].queryset = Funcionario.objects.all()
        self.fields['responsavel_2_nome'].queryset = Funcionario.objects.all()
        self.fields['responsavel_3_nome'].queryset = Funcionario.objects.all()

        # Deixar os campos de responsáveis não obrigatórios
        self.fields['responsavel_1_nome'].required = False
        self.fields['responsavel_2_nome'].required = False
        self.fields['responsavel_3_nome'].required = False
        self.fields['responsavel_1_cargo'].required = False
        self.fields['responsavel_2_cargo'].required = False
        self.fields['responsavel_3_cargo'].required = False

        # Preenchimento automático dos cargos (feito no front-end via AJAX)
        if 'funcionario' in self.data:
            funcionario_id = self.data.get('funcionario')
            try:
                funcionario = Funcionario.objects.get(id=funcionario_id)
                self.fields['responsavel_1_cargo'].initial = funcionario.cargo_atual
                self.fields['responsavel_2_cargo'].initial = funcionario.cargo_atual
                self.fields['responsavel_3_cargo'].initial = funcionario.cargo_atual
            except (ValueError, Funcionario.DoesNotExist):
                pass
        elif self.instance.pk:
            # Para edições de uma avaliação existente
            self.fields['responsavel_1_cargo'].initial = self.instance.funcionario.cargo_atual
            self.fields['responsavel_2_cargo'].initial = self.instance.funcionario.cargo_atual
            self.fields['responsavel_3_cargo'].initial = self.instance.funcionario.cargo_atual

class AvaliacaoExperienciaForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'data_avaliacao', 'funcionario', 'gerencia', 
            'adaptacao_trabalho', 'interesse', 'relacionamento_social', 
            'capacidade_aprendizagem', 'avaliado', 'avaliador', 'observacoes'
        ]
        widgets = {
            'data_avaliacao': forms.DateInput(attrs={'type': 'date'}),
        }


class AvaliacaoAnualForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'data_avaliacao', 'funcionario', 'centro_custo', 
            'gerencia', 'avaliador', 'avaliado',
            'postura_seg_trabalho', 'qualidade_produtividade', 
            'trabalho_em_equipe', 'comprometimento',
            'disponibilidade_para_mudancas', 'disciplina', 
            'rendimento_sob_pressao', 'proatividade',
            'comunicacao', 'assiduidade', 'observacoes'
        ]
        widgets = {
            'data_avaliacao': forms.DateInput(attrs={'type': 'date'}),
        }


class JobRotationEvaluationForm(forms.ModelForm):
    class Meta:
        model = JobRotationEvaluation
        fields = '__all__' 

