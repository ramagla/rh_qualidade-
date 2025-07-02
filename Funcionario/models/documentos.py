from django.db import models
from django.utils import timezone
from .cargo import Cargo
from Funcionario.models.departamentos import Departamentos


class Documento(models.Model):
    """
    Representa um documento controlado com dados de recuperação, status,
    armazenamento, descarte e histórico de revisões.
    """

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

    nome = models.CharField(max_length=100, verbose_name="Nome do Documento")
    codigo = models.CharField(max_length=4, verbose_name="Código")
    arquivo = models.FileField(upload_to="documentos/", blank=True, null=True, verbose_name="Arquivo")
    responsavel_recuperacao = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name="cargos",
        verbose_name="Responsável pela Recuperação"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="em_revisao",
        verbose_name="Status"
    )

    coleta = models.CharField(max_length=100, blank=True, null=True, verbose_name="Método de Coleta")
    recuperacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Método de Recuperação")
    arquivo_tipo = models.CharField(
        max_length=50,
        choices=ARQUIVO_TIPO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tipo de Arquivo"
    )
    local_armazenamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Local de Armazenamento"
    )
    tempo_retencao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Tempo de Retenção"
    )
    descarte = models.CharField(
        max_length=30,
        choices=DESCARTE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Forma de Descarte"
    )
    departamentos = models.ManyToManyField(
        Departamentos,
        blank=True,
        verbose_name="Departamentos Relacionados"
    )

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']
        verbose_name_plural = "Documentos"


class RevisaoDoc(models.Model):
    """
    Histórico de revisões aplicadas a um documento, incluindo número, data,
    mudanças e status da revisão.
    """

    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    ]

    documento = models.ForeignKey(
        Documento,
        related_name="revisoes",
        on_delete=models.CASCADE,
        verbose_name="Documento"
    )
    numero_revisao = models.CharField(max_length=20, verbose_name="Número da Revisão")
    data_revisao = models.DateField(default=timezone.now, verbose_name="Data da Revisão")
    descricao_mudanca = models.TextField(verbose_name="Descrição da Mudança")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ativo",
        verbose_name="Status da Revisão"
    )

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.documento.nome}"

    class Meta:
        ordering = ["-data_revisao"]
        verbose_name_plural = "Revisões de Documento"
