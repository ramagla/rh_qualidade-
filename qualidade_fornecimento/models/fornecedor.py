from datetime import timedelta

from django.db import models
import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.core.files.uploadedfile import UploadedFile
from datetime import datetime

# 📌 Função para renomear certificado
def renomear_certificado_fornecedor(instance, filename):
    nome, ext = os.path.splitext(filename)
    fornecedor_nome = slugify(instance.nome or "fornecedor")
    data_atual = datetime.now().strftime("%Y%m%d")  # formato AAAAMMDD
    return os.path.join(
        "certificados/fornecedores",
        f"{fornecedor_nome}-{data_atual}{ext}"
    )

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if not arquivo or not isinstance(arquivo, UploadedFile):
            return
        if arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb
    
TIPO_PRODUTO = [
    ("Fita de Aço/Inox", "Fita de Aço/Inox"),
    ("Arame de Aço", "Arame de Aço"),
    ("Arame de inox", "Arame de inox"),
    ("Calibração", "Calibração"),
    ("Trat. Superficial", "Trat. Superficial"),
    ("Material do Cliente", "Material do Cliente"),
]

TIPO_CERTIFICACAO = [
    ("ISO 9001", "ISO 9001"),
    ("IATF16949", "IATF16949"),
    ("NBR-ISO 17025 RBC", "NBR-ISO 17025 RBC"),
    ("AUDITORIA", "AUDITORIA"),
]

RISCO_AVALIACAO = [
    ("Baixo", "Baixo"),
    ("Alto", "Alto"),
    ("N/A", "N/A"),
]

TIPO_FORMULARIO = [
    ("Processo (F154)", "Processo (F154)"),
    ("CQI-11", "CQI-11"),
    ("CQI-12", "CQI-12"),
    ("CQI-9", "CQI-9"),
    ("N/A", "N/A"),
]

SIM_NAO = [
    ("Sim", "Sim"),
    ("Não", "Não"),
]

STATUS_ATIVO = [
    ("Ativo", "Ativo"),
    ("Em Homologação", "Em Homologação"),
    ("Inativo", "Inativo"),
]


class FornecedorQualificado(models.Model):
    # Informações Gerais
    nome = models.CharField(max_length=255)
    produto_servico = models.CharField(max_length=50, choices=TIPO_PRODUTO)
    data_homologacao = models.DateField(blank=True, null=True)
    ativo = models.CharField(
        max_length=20,
        choices=STATUS_ATIVO,
        default="Em Homologação",
        verbose_name="Status do Fornecedor"
    )

    # Certificação do Sistema
    tipo_certificacao = models.CharField(max_length=30, choices=TIPO_CERTIFICACAO)
    vencimento_certificacao = models.DateField(blank=True, null=True)

    # Avaliação de Risco (F211)
    risco = models.CharField(max_length=10, choices=RISCO_AVALIACAO, blank=True)
    data_avaliacao_risco = models.DateField(blank=True, null=True)
    proxima_avaliacao_risco = models.DateField(blank=True, null=True)

    # Auditoria de Processo (F154, CQIs)
    tipo_formulario = models.CharField(
        max_length=20, choices=TIPO_FORMULARIO, blank=True
    )
    data_auditoria = models.DateField(blank=True, null=True)
    proxima_auditoria = models.DateField(blank=True, null=True)
    nota_auditoria = models.FloatField(blank=True, null=True)

    # Cálculos Automáticos
    classe_frequencia = models.CharField(
        max_length=10, blank=True
    )  # A, B, C (automático)
    status = models.CharField(
        max_length=30, blank=True
    )  # Qualificado, Qualificado Condicional, Reprovado
    score = models.FloatField(blank=True, null=True)  # Baseado na certificação

    # Especialista de Segurança do Produto
    especialista_nome = models.CharField(max_length=100, blank=True)
    especialista_cargo = models.CharField(max_length=100, blank=True)
    especialista_contato = models.CharField(max_length=100, blank=True)

    # Certificados
    certificado_anexo = models.FileField(
        upload_to=renomear_certificado_fornecedor,
        blank=True,
        null=True,
        verbose_name="Certificado Anexo",
        validators=[MaxFileSizeValidator(5)],
    )
    lead_time = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Lead Time (dias)"
    )

    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Condição para "Calibração" com certificação "NBR-ISO 17025 RBC"
        # Regra para Material do Cliente → força status como Qualificado
        if self.produto_servico == "Material do Cliente":
            self.status = "Qualificado"
            self.risco = "N/A"
            self.data_avaliacao_risco = None
            self.proxima_avaliacao_risco = None
            self.tipo_formulario = ""
            self.data_auditoria = None
            self.proxima_auditoria = None
            self.nota_auditoria = None
            self.classe_frequencia = ""
            self.especialista_nome = ""
            self.especialista_contato = ""
        else:
            nota = self.nota_auditoria or 0
        if (
            self.produto_servico == "Calibração"
            and self.tipo_certificacao == "NBR-ISO 17025 RBC"
        ):
            self.vencimento_certificacao = None
            self.risco = "N/A"
            self.data_avaliacao_risco = None
            self.proxima_avaliacao_risco = None
            self.tipo_formulario = ""
            self.data_auditoria = None
            self.proxima_auditoria = None
            self.nota_auditoria = None
            self.classe_frequencia = ""
            self.status = "Qualificado"
            self.especialista_nome = ""
            self.especialista_contato = ""
        else:
            nota = self.nota_auditoria or 0

            # Se o Tipo de Auditoria for um dos CQIs, forçamos a regra
            if self.tipo_formulario in ["CQI-11", "CQI-12", "CQI-9"]:
                self.classe_frequencia = "C"
                self.status = "Qualificado"
                delta = timedelta(days=365)
                if self.data_auditoria:
                    self.proxima_auditoria = self.data_auditoria + delta
                    self.proxima_avaliacao_risco = self.proxima_auditoria
            else:
                # Regra para Classe / Frequência com base na nota (usando intervalo 0 a 100)
                if nota >= 90:
                    self.classe_frequencia = "A"
                    delta = timedelta(days=3 * 365)
                elif nota >= 50:
                    self.classe_frequencia = "B"
                    delta = timedelta(days=2 * 365)
                else:
                    self.classe_frequencia = "C"
                    delta = timedelta(days=365)

                if self.data_auditoria:
                    self.proxima_auditoria = self.data_auditoria + delta
                    self.proxima_avaliacao_risco = self.proxima_auditoria

                # Regra para o Status com base na nota
                if nota >= 90:
                    self.status = "Qualificado"
                elif nota >= 50:
                    self.status = "Qualificado Condicional"
                else:
                    self.status = "Reprovado"

        # Regra para o Score com base na certificação (aplica-se em todos os casos)
        if self.tipo_certificacao == "ISO 9001":
            self.score = 90
        elif self.tipo_certificacao == "IATF16949":
            self.score = 100
        else:
            self.score = 80

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
