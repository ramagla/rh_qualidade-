from django.db import models
from django.utils import timezone


class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    cbo = models.CharField(max_length=20)
    descricao_arquivo = models.FileField(upload_to='cargos/', blank=True, null=True)
    departamento = models.CharField(max_length=100, verbose_name='Departamento')  # Novo campo de departamento

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
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
    foto = models.ImageField(upload_to='fotos_funcionarios/', blank=True, null=True)  # Novo campo para foto
    curriculo = models.FileField(upload_to='curriculos_funcionarios/', blank=True, null=True)  # Novo campo para currículo

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
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='treinamentos')
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

