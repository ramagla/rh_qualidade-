import os
from django.db import models
from django.utils.text import slugify
from .cargo import Cargo

# Função para renomear o arquivo de currículo
def renomear_curriculo(instance, filename):   
    # Extrai a extensão do arquivo
    nome, extensao = os.path.splitext(filename)
    # Cria um nome com base no nome do funcionário e no número de registro
    novo_nome = f"{slugify(instance.nome)}-{instance.numero_registro}{extensao}"
    # Retorna o caminho completo onde o arquivo será salvo
    return os.path.join('curriculos_funcionarios', novo_nome)

# Modelo Funcionario
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
    data_integracao = models.DateField(blank=True, null=True)
    responsavel = models.CharField(max_length=100, blank=True, null=True)
    cargo_responsavel = models.CharField(max_length=100)
    escolaridade = models.CharField(max_length=100, blank=True, null=True)
    experiencia_profissional = models.CharField(max_length=3, choices=EXPERIENCIA_CHOICES, default='Sim')
    updated_at = models.DateTimeField(auto_now=True)
    foto = models.ImageField(upload_to='fotos_funcionarios/', blank=True, null=True)
    curriculo = models.FileField(upload_to=renomear_curriculo, blank=True, null=True)
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