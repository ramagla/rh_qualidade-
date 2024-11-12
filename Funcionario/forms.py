from datetime import timedelta  # Correto
from django.utils import timezone  # Já está correto

from django import forms
from .models import Funcionario, Cargo, Revisao, Treinamento,ListaPresenca,AvaliacaoTreinamento,JobRotationEvaluation,AvaliacaoExperiencia, AvaliacaoAnual,Comunicado
from django_ckeditor_5.widgets import CKEditor5Widget
from django.forms.widgets import DateInput

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
        fields = '__all__'




class AvaliacaoTreinamentoForm(forms.ModelForm):
    # Campos do formulário
    pergunta_1 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        widget=forms.RadioSelect,
        required=False,
        label="Grau de conhecimento atual dos participantes da metodologia"
    )
    pergunta_2 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_APLICACAO,
        widget=forms.RadioSelect,
        required=False,
        label="Aplicação dos conceitos da metodologia"
    )
    pergunta_3 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_RESULTADOS,
        widget=forms.RadioSelect,
        required=False,
        label="Resultados obtidos com a aplicação da metodologia"
    )
    descricao_melhorias = forms.CharField(
        widget=forms.Textarea(attrs={'style': 'height: 100px'}),
        required=True,
        label="Descreva as melhorias obtidas/resultados"
    )
    avaliacao_geral = forms.IntegerField(
        widget=forms.HiddenInput(),  # Mude para IntegerField
        required=False  # Ajuste se este campo não for obrigatório no formulário
    )

    class Meta:
        model = AvaliacaoTreinamento
        fields = '__all__'
        widgets = {
            'responsavel_1': forms.Select(attrs={'class': 'form-select'}),
            'responsavel_2': forms.Select(attrs={'class': 'form-select'}),
            'responsavel_3': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'treinamento': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(AvaliacaoTreinamentoForm, self).__init__(*args, **kwargs)

        # Definindo o queryset para o campo 'treinamento'
        self.fields['treinamento'].queryset = ListaPresenca.objects.all()
        self.fields['treinamento'].label = 'Treinamento/Curso'

        # Configurando o queryset para campos de responsáveis
        # Agora os responsáveis são ForeignKeys para o modelo Funcionario
        self.fields['responsavel_1'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_1'].required = False  # Definindo como opcional

        self.fields['responsavel_2'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_2'].required = False  # Definindo como opcional

        self.fields['responsavel_3'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_3'].required = False  # Definindo como opcional

        # Ajustando rótulos
        self.fields['responsavel_1'].label = "Primeiro Responsável (opcional)"
        self.fields['responsavel_2'].label = "Segundo Responsável (opcional)"
        self.fields['responsavel_3'].label = "Terceiro Responsável (opcional)"


class AvaliacaoExperienciaForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoExperiencia
        fields = '__all__' 
        widgets = {
            'data_avaliacao': forms.DateInput(attrs={'type': 'date'}),
        }


class AvaliacaoAnualForm(forms.ModelForm):
    avaliacao_global_avaliador = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    avaliacao_global_avaliado = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    class Meta:
        model = AvaliacaoAnual
        fields = '__all__' 
        widgets = {
            'data_avaliacao': forms.DateInput(attrs={'type': 'date'}),
        }

class JobRotationEvaluationForm(forms.ModelForm):
    treinamentos_requeridos = forms.CharField(widget=CKEditor5Widget(), required=False)
    treinamentos_propostos = forms.CharField(widget=CKEditor5Widget(), required=False)
    avaliacao_gestor = forms.CharField(widget=CKEditor5Widget(), required=False)
    avaliacao_funcionario = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = JobRotationEvaluation
        fields = '__all__'

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < timezone.now().date():  # Caso queira validar se a data é futura
            raise forms.ValidationError("A data de início não pode ser no passado.")
        return data_inicio

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Preencher campos automaticamente baseado no funcionário selecionado
        if instance.funcionario:
            # Atribui o cargo atual e a área atual do funcionário
            instance.cargo_atual = instance.funcionario.cargo_atual
            instance.area_atual = instance.funcionario.local_trabalho  # A área atual é o 'local_trabalho' de Funcionario
            instance.escolaridade = instance.funcionario.escolaridade  # Atribui escolaridade

            # Calcular o término previsto (adiciona 60 dias à data de início)
            if instance.data_inicio:
                instance.termino_previsto = instance.data_inicio + timedelta(days=60)

            # Preenche a última avaliação, se necessário
            try:
                ultima_avaliacao = instance.funcionario.avaliacaoanual_set.latest('data_avaliacao')
                instance.data_ultima_avaliacao = ultima_avaliacao.data_avaliacao
                classificacao = ultima_avaliacao.calcular_classificacao()
                instance.status_ultima_avaliacao = classificacao['status']
            except AvaliacaoAnual.DoesNotExist:
                instance.data_ultima_avaliacao = None  # Se não houver avaliação, deixe como None
                instance.status_ultima_avaliacao = 'Indeterminado'  # Ou outro status default

            # Preenche a descrição do cargo, se disponível
            if instance.funcionario.cargo_atual:
                instance.descricao_cargo = instance.funcionario.cargo_atual.descricao_arquivo  # Atribui descrição do cargo

            # Preenche a lista de cursos realizados, caso haja
            cursos = instance.funcionario.treinamentos.filter(status='concluido')  # Apenas cursos concluídos
            cursos_realizados = [curso.nome_curso for curso in cursos]  # Cria uma lista com os nomes dos cursos
            instance.cursos_realizados = cursos_realizados  # Atribui à lista de cursos realizados

        if commit:
            instance.save()
        return instance
    


class ComunicadoForm(forms.ModelForm):
    descricao = forms.CharField(widget=CKEditor5Widget(), required=True)

    class Meta:
        model = Comunicado
        fields = ['data', 'assunto', 'descricao', 'tipo', 'departamento_responsavel', 'lista_assinaturas']

        widgets = {
            'data': DateInput(attrs={'class': 'form-control', 'type': 'date', 'value': ''}),  # Aqui, adicionamos 'value' como vazio
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),           
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'departamento_responsavel': forms.TextInput(attrs={'class': 'form-control'}),
        }