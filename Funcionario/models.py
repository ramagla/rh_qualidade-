from django.db import models
from django.utils import timezone
from datetime import timedelta
from django_ckeditor_5.fields import CKEditor5Field



class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    numero_dc = models.CharField(max_length=4)
    descricao_arquivo = models.FileField(upload_to='cargos/', blank=True, null=True)
    departamento = models.CharField(max_length=100, verbose_name='Departamento')

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]

    EXPERIENCIA_CHOICES = [
        ('Sim', 'Sim, (Anexar Curriculum ou cópia da Carteira Profissional no prontuário)'),
        ('Não', 'Não, (Justificar através da Avaliação Prática da Atividade, devidamente assinada)'),
    ]
    
    nome = models.CharField(max_length=100)
    data_admissao = models.DateField()
    cargo_inicial = models.ForeignKey(Cargo, related_name='cargo_inicial_funcionarios', on_delete=models.CASCADE)
    cargo_atual = models.ForeignKey(Cargo, related_name='cargo_atual_funcionarios', on_delete=models.CASCADE, null=True)
    numero_registro = models.CharField(max_length=20, unique=True)
    local_trabalho = models.CharField(max_length=100)
    data_integracao = models.DateField()
    responsavel = models.CharField(max_length=100)    
    cargo_responsavel = models.CharField(max_length=100)
    escolaridade = models.CharField(max_length=100, blank=True, null=True)
    experiencia_profissional = models.CharField(max_length=3, choices=EXPERIENCIA_CHOICES, default='Sim')
    updated_at = models.DateTimeField(auto_now=True)
    foto = models.ImageField(upload_to='fotos_funcionarios/', blank=True, null=True)
    curriculo = models.FileField(upload_to='curriculos_funcionarios/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo')
    formulario_f146 = models.FileField(upload_to='formularios_f146/', blank=True, null=True)
   
    def __str__(self):
        return self.nome
    
    def atualizar_escolaridade(self):
        # Define a hierarquia das formações
        hierarchy = {
            'tecnico': 1,
            'graduacao': 2,
            'pos-graduacao': 3,
            'mestrado': 4,
            'doutorado': 5,
        }

        # Filtra os treinamentos concluídos e que não são de capacitação, ordena pela hierarquia
        treinamentos_concluidos = self.treinamentos.filter(status='concluido').exclude(categoria='capacitacao')
        treinamento_mais_alto = None
        maior_nivel = 0

        for treinamento in treinamentos_concluidos:
            nivel = hierarchy.get(treinamento.categoria, 0)
            if nivel > maior_nivel:
                maior_nivel = nivel
                treinamento_mais_alto = treinamento

        # Atualiza o campo escolaridade com a descrição da formação mais alta
        if treinamento_mais_alto:
            self.escolaridade = treinamento_mais_alto.get_categoria_display()
            self.save()
        else:
            self.escolaridade = None
            self.save()


class Revisao(models.Model):
    cargo = models.ForeignKey(Cargo, related_name='revisoes', on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=20)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.cargo.nome}"
    
class Treinamento(models.Model):
    TIPO_TREINAMENTO_CHOICES = [
        ('interno', 'Interno'),
        ('externo', 'Externo'),
    ]
    
    CATEGORIA_CHOICES = [
        ('capacitacao', 'Capacitação'),
        ('tecnico', 'Técnico'),
        ('graduacao', 'Graduação'),
        ('treinamento', 'Treinamento'),
    ]
    
    STATUS_CHOICES = [
        ('concluido', 'Concluído'),
        ('trancado', 'Trancado'),
        ('cursando', 'Cursando'),
        ('requirido', 'Requirido'),
    ]
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='treinamentos')
    tipo = models.CharField(max_length=50, choices=TIPO_TREINAMENTO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    nome_curso = models.CharField(max_length=255)
    instituicao_ensino = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='cursando')  # Campo de status
    data_inicio = models.DateField()
    data_fim = models.DateField()
    carga_horaria = models.CharField(max_length=50)
    anexo = models.FileField(upload_to='anexos/', blank=True, null=True)

    def __str__(self):
        return self.nome_curso

class ListaPresenca(models.Model):
    TIPO_CHOICES = [
        ('Treinamento', 'Treinamento'),
        ('Curso', 'Curso'),
        ('Divulgacao', 'Divulgação')
    ]
    
    treinamento = models.CharField(max_length=255, choices=TIPO_CHOICES)
    data_realizacao = models.DateField(default='2024-01-01')
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    instrutor = models.CharField(max_length=255)
    duracao = models.DecimalField(max_digits=5, decimal_places=2)
    necessita_avaliacao = models.BooleanField(default=False)
    lista_presenca = models.FileField(upload_to='listas_presenca/', null=True, blank=True)
    participantes = models.ManyToManyField('Funcionario', related_name='participantes')
    assunto = models.CharField(max_length=255, null=True, blank=True)  # Permite valores nulos
    descricao = CKEditor5Field(config_name='default')

    def duracao_formatada(self):
        total_minutes = int(self.duracao * 60)  # Converte horas para minutos
        hours = total_minutes // 60  # Divide por 60 para obter as horas inteiras
        minutes = total_minutes % 60  # Resto da divisão para obter os minutos
        return f"{hours}h {minutes}m"

    def __str__(self):
        return f"Lista de Presença - {self.treinamento} ({self.data_realizacao})"
    
class AvaliacaoTreinamento(models.Model):
    OPCOES_CONHECIMENTO = [
        (1, 'Não possui conhecimento mínimo da metodologia para sua aplicação.'),
        (2, 'Apresenta deficiências nos conceitos, o que compromete a aplicação.'),
        (3, 'Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.'),
        (4, 'Possui domínio necessário da metodologia e a utiliza adequadamente.'),
        (5, 'Possui completo domínio e utiliza a metodologia com excelência.')
    ]

    OPCOES_APLICACAO = [
        (1, 'Está muito abaixo do esperado.'),
        (2, 'Aplicação está abaixo do esperado.'),
        (3, 'Aplicação é razoável, mas não dentro do esperado.'),
        (4, 'Aplicação está adequada e corresponde às expectativas.'),
        (5, 'Aplicação excede as expectativas.')
    ]

    OPCOES_RESULTADOS = [
        (1, 'Nenhum resultado foi obtido efetivamente até o momento.'),
        (2, 'As melhorias obtidas estão muito abaixo do esperado.'),
        (3, 'As melhorias obtidas são consideráveis, mas não dentro do esperado.'),
        (4, 'As melhorias obtidas são boas e estão dentro do esperado.'),
        (5, 'As melhorias obtidas excederam as expectativas.')
    ]


    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    treinamento = models.ForeignKey(ListaPresenca, on_delete=models.CASCADE, related_name="avaliacoes")

    data_avaliacao = models.DateField()
    periodo_avaliacao = models.IntegerField(default=60)  # Novo campo para o período em dias

    def get_status_prazo(self):
        # Calcula a data limite adicionando o período ao dia da avaliação
        data_limite = self.data_avaliacao + timedelta(days=self.periodo_avaliacao)
        
        # Compara a data atual com a data limite
        if timezone.now().date() <= data_limite:
            return "Dentro do Prazo"
        return "Em Atraso"


    # Substituímos os campos de texto por ForeignKey relacionados ao modelo Funcionario
    responsavel_1 = models.ForeignKey('Funcionario', on_delete=models.SET_NULL, null=True, blank=True, related_name='avaliacoes_responsavel_1')
    responsavel_2 = models.ForeignKey('Funcionario', on_delete=models.SET_NULL, null=True, blank=True, related_name='avaliacoes_responsavel_2')
    responsavel_3 = models.ForeignKey('Funcionario', on_delete=models.SET_NULL, null=True, blank=True, related_name='avaliacoes_responsavel_3')

    pergunta_1 = models.IntegerField(choices=OPCOES_CONHECIMENTO)
    pergunta_2 = models.IntegerField(choices=OPCOES_APLICACAO)
    pergunta_3 = models.IntegerField(choices=OPCOES_RESULTADOS)

    descricao_melhorias = models.TextField(default="Nenhuma melhoria descrita")
    avaliacao_geral = models.IntegerField(choices=[
        (1, 'Pouco eficaz'), 
        (2, 'Eficaz'), 
        (3, 'Razoável'), 
        (4, 'Bom'), 
        (5, 'Muito eficaz')
    ])
    

class AvaliacaoExperiencia(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    avaliador = models.ForeignKey(
        Funcionario,
        related_name='avaliacoes_experiencia',
        on_delete=models.CASCADE
    )    
    avaliado = models.ForeignKey(Funcionario, related_name='avaliado_experiencia', on_delete=models.CASCADE, null=True, blank=True)
    gerencia = models.CharField(max_length=100, blank=True, null=True)

    # Campos específicos para o questionário de experiência
    adaptacao_trabalho = models.IntegerField(null=True, blank=True)
    interesse = models.IntegerField(null=True, blank=True)
    relacionamento_social = models.IntegerField(null=True, blank=True)
    capacidade_aprendizagem = models.IntegerField(null=True, blank=True)

    # Observações e orientação
    observacoes = models.TextField(blank=True, null=True)
    orientacao = models.CharField(max_length=100, blank=True, null=True)

    @property
    def get_status_avaliacao(self):
        if self.orientacao == "Efetivar":
            return "😃 Efetivar"
        elif self.orientacao == "Encaminhar p/ Treinamento":
            return "😊 Treinamento"
        elif self.orientacao == "Desligar":
            return "😕 Desligar"
        return "Indeterminado"

    def get_status_prazo(self):
        hoje = timezone.now().date()
        data_limite = self.data_avaliacao + timedelta(days=30)
        return "Dentro do Prazo" if data_limite >= hoje else "Em Atraso"

    def __str__(self):
        return f"Avaliação de Experiência de {self.funcionario} em {self.data_avaliacao}"

class AvaliacaoAnual(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    centro_custo = models.CharField(max_length=100, blank=True, null=True)
    
    # Campos do questionário
    postura_seg_trabalho = models.IntegerField(blank=True, null=True)
    qualidade_produtividade = models.IntegerField(blank=True, null=True)
    trabalho_em_equipe = models.IntegerField(blank=True, null=True)
    comprometimento = models.IntegerField(blank=True, null=True)
    disponibilidade_para_mudancas = models.IntegerField(blank=True, null=True)
    disciplina = models.IntegerField(blank=True, null=True)
    rendimento_sob_pressao = models.IntegerField(blank=True, null=True)
    proatividade = models.IntegerField(blank=True, null=True)
    comunicacao = models.IntegerField(blank=True, null=True)
    assiduidade = models.IntegerField(blank=True, null=True)
    avaliacao_global_avaliador = models.TextField(blank=True, null=True)
    avaliacao_global_avaliado = models.TextField(blank=True, null=True)

    def calcular_classificacao(self):
        total_pontos = (
            (self.postura_seg_trabalho or 0) + 
            (self.qualidade_produtividade or 0) + 
            (self.trabalho_em_equipe or 0) + 
            (self.comprometimento or 0) +
            (self.disponibilidade_para_mudancas or 0) + 
            (self.disciplina or 0) + 
            (self.rendimento_sob_pressao or 0) + 
            (self.proatividade or 0) + 
            (self.comunicacao or 0) + 
            (self.assiduidade or 0)
        )

        if total_pontos == 0:
            return {'percentual': 0, 'status': 'Indeterminado'}

        percentual = (total_pontos / 40) * 100  # Assume que o total máximo de pontos é 40
        status = ''

        if percentual <= 25:
            status = 'Ruim'
        elif percentual <= 45:
            status = 'Regular'
        elif percentual <= 84:
            status = 'Bom'
        else:
            status = 'Ótimo'

        return {'percentual': percentual, 'status': status}




  
class JobRotationEvaluation(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="job_rotation_evaluations")
    local_trabalho = models.CharField(max_length=100, null=True, blank=True)
    cargo_atual = models.ForeignKey(Cargo, related_name='job_rotation_evaluations_cargo', on_delete=models.CASCADE, null=True, blank=True)
    competencias = models.TextField(null=True, blank=True)
    data_ultima_avaliacao = models.DateField(null=True, blank=True)
    status_ultima_avaliacao = models.CharField(max_length=50, null=True, blank=True)
    cursos_realizados = models.JSONField(default=list, null=True, blank=True)  # Lista de cursos realizados
    escolaridade = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100)
    nova_funcao = models.ForeignKey(Cargo, related_name='nova_funcao', on_delete=models.SET_NULL, null=True, blank=True)
    data_inicio = models.DateField()
    termino_previsto = models.DateField(editable=False, null=True, blank=True)
    gestor_responsavel = models.ForeignKey(Funcionario, related_name='gestor_responsavel', on_delete=models.SET_NULL, null=True)
    descricao_cargo = models.TextField(null=True, blank=True)
    treinamentos_requeridos = models.TextField(blank=True)
    treinamentos_propostos = models.TextField(blank=True)
    avaliacao_gestor = models.TextField(blank=True)
    avaliacao_funcionario = models.TextField(blank=True)
    avaliacao_rh = models.CharField(
        max_length=20,
        choices=[('Apto', 'Apto'), ('Inapto', 'Inapto'), ('Prorrogar TN', 'Prorrogar TN'), ('EmProgresso', 'Em Progresso')],  # Adicionado "Em Progresso"
    )
    disponibilidade_vaga = models.BooleanField(default=False)

    def __str__(self):
        return f"Avaliação de Job Rotation - {self.funcionario.nome}"


class Comunicado(models.Model):
    TIPO_CHOICES = [
        ('Auditoria', 'Auditoria'),
        ('Conscientizacao', 'Conscientização'),
        ('Melhoria', 'Melhoria'),
        ('Organizacao/Processos', 'Organização / Processos'),
        ('Recursos Humanos', 'Recursos Humanos'),
        ('Visita de Cliente', 'Visita de Cliente'),
    ]
    
    data = models.DateField(default=timezone.now)
    assunto = models.CharField(max_length=100)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    departamento_responsavel = models.CharField(max_length=100)
    lista_assinaturas = models.FileField(upload_to='assinaturas/', null=True, blank=True)

    def __str__(self):
        return f"Comunicado {self.id} - {self.assunto}"
    

class AtualizacaoSistema(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    previsao = models.DateField()
    versao = models.CharField(max_length=20)  # Adiciona o campo versão

    def __str__(self):
        return f"{self.versao} - {self.titulo}"
    
class IntegracaoFuncionario(models.Model):
    funcionario = models.ForeignKey('Funcionario', on_delete=models.CASCADE)
    grupo_whatsapp = models.BooleanField(default=False)
    requer_treinamento = models.BooleanField(default=False)
    treinamentos_requeridos = models.TextField(blank=True, null=True)
    data_integracao = models.DateField(default=timezone.now)

    @property
    def departamento(self):
        return self.funcionario.local_trabalho

    def save(self, *args, **kwargs):
        # Verifica se o campo data_integracao foi alterado
        if self.pk:
            original = IntegracaoFuncionario.objects.get(pk=self.pk)
            if original.data_integracao != self.data_integracao:
                # Atualiza a data_integracao no modelo Funcionario
                self.funcionario.data_integracao = self.data_integracao
                self.funcionario.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Integração - {self.funcionario.nome} ({self.data_integracao})"


class Settings(models.Model):
    nome_empresa = models.CharField(max_length=100, default="BRAS-MOL MOLAS & ESTAMPADOS LTDA")
    cep = models.CharField(max_length=20, default="08579000")
    endereco = models.CharField(max_length=150, default="BONSUCESSO, DO, 1961 - RIO ABAIXO - Itaquaquecetuba / SP")
    telefone = models.CharField(max_length=20, default="1146482611")
    email = models.EmailField(default="rh@brasmol.com.br")
    cnpj = models.CharField(max_length=20, default="61.296.901/0002-48")
    
    # Campos para os logos
    logo_claro = models.ImageField(upload_to='logos/', null=True, blank=True)
    logo_escuro = models.ImageField(upload_to='logos/', null=True, blank=True)

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"

    def save(self, *args, **kwargs):
            # Garante que haja apenas um registro de configurações
            if not Settings.objects.filter(pk=self.pk).exists() and Settings.objects.exists():
                self.pk = Settings.objects.first().pk
            super(Settings, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome_empresa
    

class Evento(models.Model):
    TIPOS_EVENTO = [
        ("avaliacao_desempenho", "Avaliação de Desempenho"),
        ("feriado", "Feriado"),
        ("ponte", "Ponte"),
        ("confraternizacao", "Confraternização"),
        ("recesso", "Recesso"),
        ("auditoria_sgs", "Auditoria SGS"),
        ("auditoria_interna", "Auditoria Interna"),
        ("sipat", "SIPAT"),
        ("inventario", "Inventário"),
    ]
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField()  # Alterado para DateField
    data_fim = models.DateField()      # Alterado para DateField
    cor = models.CharField(max_length=7, default='#3788d8')
    tipo = models.CharField(max_length=20, choices=TIPOS_EVENTO, default="avaliacao_desempenho")  # Campo de tipo

    def __str__(self):
        return self.titulo