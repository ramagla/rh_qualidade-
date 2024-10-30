from django.db import models
from django.utils import timezone


class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    numero_dc = models.CharField(max_length=20)  # Substitui 'cbo' por 'numero_dc'
    descricao_arquivo = models.FileField(upload_to='cargos/', blank=True, null=True)
    departamento = models.CharField(max_length=100, verbose_name='Departamento')  # Novo campo de departamento

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]
    
    nome = models.CharField(max_length=100)
    data_admissao = models.DateField()
    cargo_inicial = models.ForeignKey(Cargo, related_name='cargo_inicial_funcionarios', on_delete=models.CASCADE)
    cargo_atual = models.ForeignKey(Cargo, related_name='cargo_atual_funcionarios', on_delete=models.CASCADE)
    numero_registro = models.CharField(max_length=20, unique=True)
    local_trabalho = models.CharField(max_length=100)
    data_integracao = models.DateField()
    responsavel = models.CharField(max_length=100)    
    cargo_responsavel = models.CharField(max_length=100)
    escolaridade = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    foto = models.ImageField(upload_to='fotos_funcionarios/', blank=True, null=True)
    curriculo = models.FileField(upload_to='curriculos_funcionarios/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo')  # Novo campo de status
    formulario_f146 = models.FileField(upload_to='formularios_f146/', blank=True, null=True)  # Novo campo de upload para o formulário F146

    def __str__(self):
        return self.nome


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
    ]
    
    STATUS_CHOICES = [
        ('concluido', 'Concluído'),
        ('trancado', 'Trancado'),
        ('cursando', 'Cursando'),
    ]
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='treinamentos')
    tipo = models.CharField(max_length=50, choices=TIPO_TREINAMENTO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    nome_curso = models.CharField(max_length=255)
    instituicao_ensino = models.CharField(max_length=255, default="Não Informada")
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
    descricao = models.TextField()  # Novo campo

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
    # treinamento = models.ForeignKey(Treinamento, on_delete=models.CASCADE, related_name="avaliacoes")
    treinamento = models.ForeignKey(ListaPresenca, on_delete=models.CASCADE, related_name="avaliacoes")

    data_avaliacao = models.DateField()
    periodo_avaliacao = models.IntegerField(default=60)  # Novo campo para o período em dias


    responsavel_1_nome = models.CharField(max_length=100)
    responsavel_1_cargo = models.CharField(max_length=100)
    responsavel_2_nome = models.CharField(max_length=100)
    responsavel_2_cargo = models.CharField(max_length=100)
    responsavel_3_nome = models.CharField(max_length=100)
    responsavel_3_cargo = models.CharField(max_length=100)

    pergunta_1 = models.IntegerField(choices=OPCOES_CONHECIMENTO)
    pergunta_2 = models.IntegerField(choices=OPCOES_APLICACAO)
    pergunta_3 = models.IntegerField(choices=OPCOES_RESULTADOS)

    descricao_melhorias = models.TextField(default="Nenhuma melhoria descrita")
    avaliacao_geral = models.IntegerField(choices=[(1, 'Pouco eficaz'), (2, '2'), (3, '3'), (4, '4'), (5, 'Muito eficaz')], default=3)

from django.db import models

class AvaliacaoDesempenho(models.Model):
    TIPO_CHOICES = [
        ('EXPERIENCIA', 'Experiência'),
        ('ANUAL', 'Anual'),
    ]
    
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    centro_custo = models.CharField(max_length=100, blank=True, null=True)
    gerencia = models.CharField(max_length=100, blank=True, null=True)
    avaliador = models.ForeignKey(Funcionario, related_name='avaliador', on_delete=models.CASCADE)
    avaliado = models.ForeignKey(Funcionario, related_name='avaliado', on_delete=models.CASCADE)

    # Campos para o questionário de avaliação anual
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

    # Campos para o questionário de experiência
    adaptacao_trabalho = models.IntegerField(null=True, blank=True)
    interesse = models.IntegerField(null=True, blank=True)
    relacionamento_social = models.IntegerField(null=True, blank=True)
    capacidade_aprendizagem = models.IntegerField(null=True, blank=True)

    # Observações e orientação
    observacoes = models.TextField(blank=True, null=True)
    orientacao = models.CharField(max_length=100, blank=True, null=True)
    
    # Novo campo para avaliação geral
    avaliacao_geral = models.IntegerField(
        choices=[(1, 'Pouco eficaz'), (2, '2'), (3, '3'), (4, '4'), (5, 'Muito eficaz')],
        default=3
    )

    def calcular_classificacao(self):
        postura = self.postura_seg_trabalho or 0
        qualidade = self.qualidade_produtividade or 0
        trabalho = self.trabalho_em_equipe or 0
        comprometimento = self.comprometimento or 0
        disponibilidade = self.disponibilidade_para_mudancas or 0
        disciplina = self.disciplina or 0
        rendimento = self.rendimento_sob_pressao or 0
        proatividade = self.proatividade or 0
        comunicacao = self.comunicacao or 0
        assiduidade = self.assiduidade or 0

        total_pontos = (
            postura + qualidade + trabalho + comprometimento +
            disponibilidade + disciplina + rendimento + proatividade +
            comunicacao + assiduidade
        )

        if total_pontos == 0:
            return 'Indeterminado'

        percentual = (total_pontos / 40) * 100

        if 25 <= percentual <= 45:
            return 'Ruim'
        elif 46 <= percentual <= 65:
            return 'Regular'
        elif 66 <= percentual <= 84:
            return 'Bom'
        elif 85 <= percentual <= 100:
            return 'Ótimo'
        else:
            return 'Indeterminado'

    def get_status_avaliacao(self):
        if self.tipo == 'ANUAL':
            if self.avaliacao_geral <= 2:
                return "Pouco Eficaz"
            elif 3 <= self.avaliacao_geral <= 4:
                return "Eficaz"
            else:
                return "Muito Eficaz"
        elif self.tipo == 'EXPERIENCIA':
            if self.orientacao == "Efetivar":
                return "😃 Efetivar"
            elif self.orientacao == "Encaminhar p/ Treinamento":
                return "😊 Treinamento"
            elif self.orientacao == "Desligar":
                return "😕 Desligar"
            else:
                return "Indefinido"
        return "Indeterminado"






class AvaliacaoExperiencia(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    gerencia = models.CharField(max_length=100, blank=True, null=True)
    adaptacao_trabalho = models.IntegerField(null=True, blank=True)
    interesse = models.IntegerField(null=True, blank=True)
    relacionamento_social = models.IntegerField(null=True, blank=True)
    capacidade_aprendizagem = models.IntegerField(null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)

def calcular_classificacao(self):
    # Usa o método get para garantir que, se o campo for None, um valor padrão de 0 seja utilizado
    postura = self.postura_seg_trabalho or 0
    qualidade = self.qualidade_produtividade or 0
    trabalho = self.trabalho_em_equipe or 0
    comprometimento = self.comprometimento or 0
    disponibilidade = self.disponibilidade_para_mudancas or 0
    disciplina = self.disciplina or 0
    rendimento = self.rendimento_sob_pressao or 0
    proatividade = self.proatividade or 0
    comunicacao = self.comunicacao or 0
    assiduidade = self.assiduidade or 0

    total_pontos = (
        postura + qualidade + trabalho + comprometimento +
        disponibilidade + disciplina + rendimento + proatividade +
        comunicacao + assiduidade
    )

    # Evita a divisão por zero
    if total_pontos == 0:
        return 'Indeterminado'

    percentual = (total_pontos / 40) * 100

    if 25 <= percentual <= 45:
        return 'Ruim'
    elif 46 <= percentual <= 65:
        return 'Regular'
    elif 66 <= percentual <= 84:
        return 'Bom'
    elif 85 <= percentual <= 100:
        return 'Ótimo'
    else:
        return 'Indeterminado'


class AvaliacaoAnual(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    centro_custo = models.CharField(max_length=100, blank=True, null=True)
    gerencia = models.CharField(max_length=100, blank=True, null=True)
    avaliador = models.ForeignKey(Funcionario, related_name='avaliador', on_delete=models.CASCADE)
    avaliado = models.ForeignKey(Funcionario, related_name='avaliacoes_desempenho', on_delete=models.CASCADE)

    postura_seg_trabalho = models.IntegerField()
    qualidade_produtividade = models.IntegerField()
    trabalho_em_equipe = models.IntegerField()
    comprometimento = models.IntegerField()
    disponibilidade_para_mudancas = models.IntegerField()
    disciplina = models.IntegerField()
    rendimento_sob_pressao = models.IntegerField()
    proatividade = models.IntegerField()
    comunicacao = models.IntegerField()
    assiduidade = models.IntegerField()
    observacoes = models.TextField(blank=True, null=True)

    def calcular_classificacao(self):
        postura = self.postura_seg_trabalho or 0
        qualidade = self.qualidade_produtividade or 0
        trabalho = self.trabalho_em_equipe or 0
        comprometimento = self.comprometimento or 0
        disponibilidade = self.disponibilidade_para_mudancas or 0
        disciplina = self.disciplina or 0
        rendimento = self.rendimento_sob_pressao or 0
        proatividade = self.proatividade or 0
        comunicacao = self.comunicacao or 0
        assiduidade = self.assiduidade or 0

        total_pontos = (
            postura +
            qualidade +
            trabalho +
            comprometimento +
            disponibilidade +
            disciplina +
            rendimento +
            proatividade +
            comunicacao +
            assiduidade
        )

        if total_pontos == 0:
            return 'Indeterminado'

        percentual = (total_pontos / 40) * 100  # Ajuste o divisor conforme necessário

        if 25 <= percentual <= 45:
            return 'Ruim'
        elif 46 <= percentual <= 65:
            return 'Regular'
        elif 66 <= percentual <= 84:
            return 'Bom'
        elif 85 <= percentual <= 100:
            return 'Ótimo'
        else:
            return 'Indeterminado'

class AvaliacaoAnual(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    centro_custo = models.CharField(max_length=100, blank=True, null=True)
    gerencia = models.CharField(max_length=100, blank=True, null=True)
    
    # Usando related_name para evitar conflitos
    avaliador = models.ForeignKey(Funcionario, related_name='avaliador_anual', on_delete=models.CASCADE)
    avaliado = models.ForeignKey(Funcionario, related_name='avaliado_anual', on_delete=models.CASCADE)

    postura_seg_trabalho = models.IntegerField()
    qualidade_produtividade = models.IntegerField()
    trabalho_em_equipe = models.IntegerField()
    comprometimento = models.IntegerField()
    disponibilidade_para_mudancas = models.IntegerField()
    disciplina = models.IntegerField()
    rendimento_sob_pressao = models.IntegerField()
    proatividade = models.IntegerField()
    comunicacao = models.IntegerField()
    assiduidade = models.IntegerField()
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Avaliação Anual para {self.funcionario.nome} em {self.data_avaliacao}"
    



class JobRotationEvaluation(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="job_rotation_evaluations")
    area_atual = models.CharField(max_length=100, null=True, blank=True)  # Campo opcional
    cargo_atual = models.ForeignKey(Cargo, related_name='job_rotation_evaluations_cargo', on_delete=models.CASCADE, null=True, blank=True)  # Campo opcional
    competencias = models.TextField(null=True, blank=True)  # Campo opcional
    data_ultima_avaliacao = models.DateField(null=True, blank=True)  # Novo campo para data da última avaliação
    status_ultima_avaliacao = models.CharField(max_length=50, null=True, blank=True, help_text="Status da última avaliação de desempenho")  # Novo campo para status da última avaliação
    cursos_realizados = models.JSONField(default=list, null=True, blank=True)
    escolaridade = models.CharField(max_length=100, null=True, blank=True)

    # Campos para Job Rotation
    area = models.CharField(max_length=100)
    nova_funcao = models.ForeignKey(Cargo, related_name='nova_funcao', on_delete=models.SET_NULL, null=True, blank=True)
    data_inicio = models.DateField()
    termino_previsto = models.DateField(editable=False, null=True, blank=True)
    gestor_responsavel = models.ForeignKey(Funcionario, related_name='gestor_responsavel', on_delete=models.SET_NULL, null=True)

    # Competências selecionadas
    descricao_cargo = models.TextField(null=True, blank=True)

    # Treinamentos Requeridos
    treinamentos_requeridos = models.TextField(blank=True)
    treinamentos_propostos = models.TextField(blank=True)

    # Avaliações
    avaliacao_gestor = models.TextField(blank=True)
    avaliacao_funcionario = models.TextField(blank=True)
    avaliacao_rh = models.CharField(
        max_length=20,
        choices=[('Apto', 'Apto'), ('Inapto', 'Inapto'), ('Prorrogar TN', 'Prorrogar TN')]
    )
    dias_prorrogacao = models.IntegerField(default=0, null=True, blank=True)
    disponibilidade_vaga = models.BooleanField(default=False)

    def __str__(self):
        return f"Avaliação de Job Rotation - {self.funcionario.nome}"