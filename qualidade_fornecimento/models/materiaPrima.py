from datetime import date, timedelta

from django.db import models

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

STATUS_CHOICES = [
    ("Aguardando F045", "Aguardando F045"),
    ("Aprovado", "Aprovado"),
    ("Aprovado Condicionalmente", "Aprovado Condicionalmente"),
    ("Reprovado", "Reprovado"),
]

from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


class RelacaoMateriaPrima(models.Model):
    nro_relatorio = models.PositiveIntegerField(unique=True, blank=True, null=True)

    materia_prima = models.ForeignKey(
        MateriaPrimaCatalogo, on_delete=models.PROTECT, verbose_name="Matéria-Prima"
    )

    data_entrada = models.DateField("Data de Entrada")
    fornecedor = models.ForeignKey(
        FornecedorQualificado, on_delete=models.PROTECT, verbose_name="Fornecedor"
    )
    nota_fiscal = models.CharField("N. Fiscal", max_length=50, blank=True, null=True)
    numero_certificado = models.CharField(
        "N° do Certificado", max_length=100, blank=True, null=True
    )

    # Novos campos booleanos com opções "Sim" e "Não"
    item_seguranca = models.BooleanField(
        "Item Segurança", choices=[(True, "Sim"), (False, "Não")], default=False
    )
    material_cliente = models.BooleanField(
        "Material do Cliente", choices=[(True, "Sim"), (False, "Não")], default=False
    )

    status = models.CharField(
        "Status", max_length=30, choices=STATUS_CHOICES, blank=True, null=True
    )

    data_prevista_entrega = models.DateField(
        "Data Prevista de Entrega", blank=True, null=True
    )
    data_renegociada_entrega = models.DateField(
        "Data de Entrega / Renegociação", blank=True, null=True
    )

    atraso_em_dias = models.IntegerField("Atraso em dias", blank=True, null=True)
    demerito_ip = models.IntegerField("Demérito (IP)", blank=True, null=True)

    anexo_certificado = models.FileField(
        upload_to="certificados/materia_prima/",
        blank=True,
        null=True,
        verbose_name="Anexo do Certificado",
    )

    anexo_f045 = models.FileField(
        upload_to="relatorios/f045/",
        blank=True,
        null=True,
        verbose_name="Relatório F045 Gerado",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None

        # Caso o objeto ainda não exista, salva para gerar o ID
        if creating and not self.pk:
            super().save(*args, **kwargs)

        # Gera o número de relatório se ainda não foi atribuído
        if creating and not self.nro_relatorio:
            self.nro_relatorio = 40000 + self.pk

        # Calcula atraso
        atraso = None
        if self.data_prevista_entrega:
            data_ref = self.data_renegociada_entrega or self.data_prevista_entrega
            atraso = (self.data_entrada - data_ref).days
        self.atraso_em_dias = max(atraso, 0) if atraso is not None else None

        # Define demérito conforme atraso
        if self.atraso_em_dias is not None:
            if self.atraso_em_dias >= 21:
                self.demerito_ip = 30
            elif self.atraso_em_dias >= 16:
                self.demerito_ip = 20
            elif self.atraso_em_dias >= 11:
                self.demerito_ip = 15
            elif self.atraso_em_dias >= 7:
                self.demerito_ip = 10
            elif self.atraso_em_dias >= 4:
                self.demerito_ip = 5
            elif self.atraso_em_dias >= 1:
                self.demerito_ip = 2
            else:
                self.demerito_ip = 0
        else:
            self.demerito_ip = None

        # Salva tudo de uma vez só
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Relatório #{self.nro_relatorio}"

    @property
    def peso_total(self):
        return self.rolos.aggregate(total=models.Sum("peso"))["total"] or 0
