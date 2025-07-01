from datetime import timedelta

from django.db import models

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
    ("Inativo", "Inativo"),
]


class FornecedorQualificado(models.Model):
    # Informações Gerais
    nome = models.CharField(max_length=255)
    produto_servico = models.CharField(max_length=50, choices=TIPO_PRODUTO)
    data_homologacao = models.DateField()
    ativo = models.CharField(
        max_length=10,
        choices=STATUS_ATIVO,
        default="Ativo",
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
        upload_to="certificados/fornecedores/", blank=True, null=True
    )
    lead_time = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Lead Time (dias)"
    )

    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Condição para "Calibração" com certificação "NBR-ISO 17025 RBC"
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
