from datetime import timedelta  # Correto
from django.utils import timezone  # Já está correto

from django import forms
from Funcionario.models import (
    Funcionario, Cargo, Revisao, Treinamento, ListaPresenca, AvaliacaoTreinamento, 
    JobRotationEvaluation, AvaliacaoExperiencia, AvaliacaoAnual, Comunicado, 
    IntegracaoFuncionario, Evento, Atividade, Documento, RevisaoDoc
)
from django_ckeditor_5.widgets import CKEditor5Widget
from django.forms.widgets import DateInput
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
    data_integracao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Data de Integração")
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

class TreinamentoForm(forms.ModelForm):
    descricao = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = Treinamento
        fields = '__all__'
        widgets = {
            'funcionarios': forms.SelectMultiple(attrs={'class': 'form-select select2'}),
            'tipo': forms.Select(choices=Treinamento.TIPO_TREINAMENTO_CHOICES, attrs={'class': 'form-select'}),
            'categoria': forms.Select(choices=Treinamento.CATEGORIA_CHOICES, attrs={'class': 'form-select'}),
            'nome_curso': forms.TextInput(attrs={'class': 'form-control'}),
            'instituicao_ensino': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(choices=Treinamento.STATUS_CHOICES, attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'carga_horaria': forms.TextInput(attrs={'class': 'form-control'}),
            'anexo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'situacao': forms.Select(choices=Treinamento.SITUACAO_CHOICES, attrs={'class': 'form-select'}),

        }

        def clean(self):
         cleaned_data = super().clean()
         status = cleaned_data.get('status')
         situacao = cleaned_data.get('situacao')

        # Validar que situação está preenchida apenas se o status for 'requerido'
         if status == 'requerido' and not situacao:
            raise forms.ValidationError({'situacao': 'A situação é obrigatória quando o status é "Requerido".'})
         return cleaned_data

class ListaPresencaForm(forms.ModelForm):
    descricao = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = ListaPresenca
        fields = '__all__'
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'participantes': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duracao': forms.TextInput(attrs={'class': 'form-control'}),
            'instrutor': forms.TextInput(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),

        }

        def clean(self):
                cleaned_data = super().clean()
                data_inicio = cleaned_data.get('data_inicio')
                data_fim = cleaned_data.get('data_fim')

                if data_inicio and data_fim and data_fim < data_inicio:
                    raise forms.ValidationError("A data de fim não pode ser anterior à data de início.")

                return cleaned_data


class AvaliacaoForm(forms.ModelForm):
     descricao_melhorias = forms.CharField(widget=CKEditor5Widget(), required=True,label="Descreva as melhorias obtidas/resultados")
     class Meta:
        model = AvaliacaoTreinamento
        fields = '__all__'


class AvaliacaoTreinamentoForm(forms.ModelForm):
    # Campo Treinamento com queryset dinâmico
    treinamento = forms.ModelChoiceField(
        queryset=Treinamento.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Treinamento/Curso",
        required=True
    )
   
    # Campos de perguntas
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
        widget=CKEditor5Widget(config_name='default'),
        required=True,
        label="Descreva as melhorias obtidas/resultados"
    )
    avaliacao_geral = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False  # Campo oculto, preenchido automaticamente no front-end
    )

    class Meta:
        model = AvaliacaoTreinamento
        fields = '__all__'
        widgets = {
            'responsavel_1': forms.Select(attrs={'class': 'form-select'}),
            'responsavel_2': forms.Select(attrs={'class': 'form-select'}),
            'responsavel_3': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Recebe o funcionário como argumento adicional
        funcionario_id = kwargs.pop('funcionario_id', None)
        super().__init__(*args, **kwargs)

        # Ajusta dinamicamente o queryset do campo treinamento
        if funcionario_id:
            self.fields['treinamento'].queryset = Treinamento.objects.filter(funcionarios__id=funcionario_id)
        else:
            self.fields['treinamento'].queryset = Treinamento.objects.none()

        # Configurando os responsáveis como opcionais
        self.fields['responsavel_1'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_1'].required = False
        self.fields['responsavel_2'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_2'].required = False
        self.fields['responsavel_3'].queryset = Funcionario.objects.filter(status="Ativo")
        self.fields['responsavel_3'].required = False

        # Ajustando os rótulos para os responsáveis
        self.fields['responsavel_1'].label = "Primeiro Responsável (opcional)"
        self.fields['responsavel_2'].label = "Segundo Responsável (opcional)"
        self.fields['responsavel_3'].label = "Terceiro Responsável (opcional)"

class AvaliacaoExperienciaForm(forms.ModelForm):
    observacoes = forms.CharField(
        widget=CKEditor5Widget(config_name='default'),  # Usando o CKEditor5Widget
        required=False,
        label="Observações"
    )

    class Meta:
        model = AvaliacaoExperiencia
        fields = '__all__'
        widgets = {
            'data_avaliacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'adaptacao_trabalho': forms.Select(
                choices=[
                    (1, "Ruim (D) - Mantém um comportamento oposto ao solicitado para seu cargo e demonstra dificuldades de aceitação."),
                    (2, "Regular (C) - Precisa de muito esforço para se integrar ao trabalho e aos requisitos da Bras-Mol."),
                    (3, "Bom (B) - Faz o possível para integrar-se ao trabalho e às características da Bras-Mol."),
                    (4, "Ótimo (A) - Identifica-se plenamente com as atividades do cargo e normas da Bras-Mol.")
                ],
                attrs={'class': 'form-select'}
            ),
            'interesse': forms.Select(
                choices=[
                    (1, "Ruim (D) - Apresenta falta de entusiasmo e vontade de trabalhar."),
                    (2, "Regular (C) - Necessitará de estímulo constante para se interessar pelo trabalho."),
                    (3, "Bom (B) - Apresenta entusiasmo adequado para o tempo na Bras-Mol."),
                    (4, "Ótimo (A) - Demonstra vivo interesse pelo novo trabalho.")
                ],
                attrs={'class': 'form-select'}
            ),
            'relacionamento_social': forms.Select(
                choices=[
                    (1, "Ruim (D) - Sente-se perdido entre os colegas e parece não ter sido aceito."),
                    (2, "Regular (C) - Esforça-se para conseguir maior integração social com os colegas."),
                    (3, "Bom (B) - Entrosou-se bem e foi aceito sem resistência."),
                    (4, "Ótimo (A) - Demonstra grande habilidade em fazer amigos, sendo muito apreciado.")
                ],
                attrs={'class': 'form-select'}
            ),
            'capacidade_aprendizagem': forms.Select(
                choices=[
                    (1, "Ruim (D) - Parece não ter capacidade mínima para o trabalho."),
                    (2, "Regular (C) - Necessita de muito esforço e repetição para compreender as tarefas."),
                    (3, "Bom (B) - Aprende suas tarefas sem dificuldades."),
                    (4, "Ótimo (A) - Habilitado para o cargo, executa sem falhas.")
                ],
                attrs={'class': 'form-select'}
            ),
            'orientacao': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'gerencia': forms.TextInput(attrs={'class': 'form-control'}),
            'avaliador': forms.Select(attrs={'class': 'form-select'}),
            'avaliado': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select select2'}),
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

class IntegracaoFuncionarioForm(forms.ModelForm):
    treinamentos_requeridos = forms.CharField(widget=CKEditor5Widget(), required=False)

    GRUPO_WHATSAPP_CHOICES = [
        (True, 'Sim'),
        (False, 'Não'),
    ]
    REQUER_TREINAMENTO_CHOICES = [
        (True, 'Sim'),
        (False, 'Não'),
    ]

    grupo_whatsapp = forms.ChoiceField(
        choices=GRUPO_WHATSAPP_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False,
        label="Grupo WhatsApp"
    )
    requer_treinamento = forms.ChoiceField(
        choices=REQUER_TREINAMENTO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False,
        label="Requer Treinamento"
    )

    treinamentos_requeridos = forms.CharField(
        widget=CKEditor5Widget(),
        required=False
    )

    class Meta:
        model = IntegracaoFuncionario
        fields = ['funcionario', 'grupo_whatsapp', 'requer_treinamento', 'treinamentos_requeridos', 'data_integracao', 'pdf_integracao']
        widgets = {
            'data_integracao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'cor', 'tipo']

    # Configurando widgets para data sem horário
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Define o tipo como 'date' para não incluir hora
            'class': 'form-control',
        }),
        label="Data de Início"
    )
    
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Define o tipo como 'date' para não incluir hora
            'class': 'form-control',
        }),
        label="Data de Fim"
    )

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['nome', 'departamento']  # Incluindo o campo 'departamento'


from .models import IndicadorDesempenho, PlanoAcaoMelhoria

class IndicadorDesempenhoForm(forms.ModelForm):
    class Meta:
        model = IndicadorDesempenho
        fields = ['nome', 'responsavel', 'objetivo', 'meta']

class PlanoAcaoMelhoriaForm(forms.ModelForm):
    class Meta:
        model = PlanoAcaoMelhoria
        fields = ['indicador', 'acao', 'responsavel', 'prazo', 'situacao']





from django import forms
from .models import Documento, RevisaoDoc

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome', 'codigo', 'arquivo', 'responsavel_recuperacao', 'status']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'responsavel_recuperacao': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class RevisaoDocForm(forms.ModelForm):
    class Meta:
        model = RevisaoDoc
        fields = ['numero_revisao', 'data_revisao', 'descricao_mudanca']
        widgets = {
            'numero_revisao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_revisao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao_mudanca': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),  # Corrige esta linha
        }

