from django.db import models
from django.utils import timezone
from .cargo import Cargo
from Funcionario.models.departamentos import Departamentos

class Documento(models.Model):
    STATUS_CHOICES = [
        ("aprovado", "Aprovado"),
        ("em_revisao", "Em Revisão"),
        ("inativo", "Inativo"),
    ]

    ARQUIVO_TIPO_CHOICES = [
        ("copia_fisica", "Cópia Física"),
        ("copia_eletronica", "Cópia Eletrônica"),
        ("copia_digitalizada", "Cópia Física / Cópia Digitalizada"),
        ("pasta_az", "Cópia Física / Pasta A-Z"),
        ("pasta_suspensa", "Cópia Física / Pasta Suspensa"),
        ("copia_eletronica_servidor", "Cópia Eletrônica (Servidor / Sistema)"),
        ("planilha_eletronica", "Planilha Eletrônica"),
        ("numero", "Cópia Eletrônica / Número"),
        ("copia_dupla", "Cópia Física / Cópia Eletrônica"),
        ("copia_servidor", "Cópia Eletrônica / Servidor"),
        ("copia_az_fisica_eletronica", "Cópia Eletrônica / Física / Pasta A-Z"),
        ("papel", "Papel"),
    ]

    DESCARTE_CHOICES = [
        ("destruido", "Destruído"),
        ("deletar", "Deletar"),
        ("obsoleto", "Obsoleto"),
        ("destruido_deletar", "Destruído / Deletar"),
        ("apagar", "Deletar / Apagar"),
        ("destruir", "Destruir"),
    ]

    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4)
    arquivo = models.FileField(upload_to="documentos/", blank=True, null=True)
    responsavel_recuperacao = models.ForeignKey(Cargo, related_name="cargos", on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="em_revisao")

    # Novos campos da Matriz de Registros da Qualidade
    coleta = models.CharField(max_length=100, blank=True, null=True)
    recuperacao = models.CharField(max_length=100, blank=True, null=True)
    arquivo_tipo = models.CharField(max_length=50, choices=ARQUIVO_TIPO_CHOICES, blank=True, null=True)
    local_armazenamento = models.CharField(max_length=100, blank=True, null=True)
    tempo_retencao = models.CharField(max_length=100, blank=True, null=True)
    descarte = models.CharField(max_length=30, choices=DESCARTE_CHOICES, blank=True, null=True)
    departamentos = models.ManyToManyField(Departamentos, blank=True)

    def __str__(self):
        return self.nome


class RevisaoDoc(models.Model):
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    ]
    documento = models.ForeignKey(Documento, related_name="revisoes", on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=20)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ativo")

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.documento.nome}"
