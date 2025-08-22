from django.db import models
from comercial.models.item import Item
from comercial.models.centro_custo import CentroDeCusto
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from tecnico.models.maquina import Maquina
from django.contrib.auth import get_user_model 
from django_ckeditor_5.fields import CKEditor5Field
from comercial.models.ferramenta import Ferramenta  # no topo, se ainda não tiver
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado  # já está carregado se necessário

from django.db import models
from comercial.models.item import Item

class RoteiroProducao(models.Model):
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    ]
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="roteiros",
        verbose_name="Item"
    )
    status = models.CharField(
        "Status",
        max_length=8,
        choices=STATUS_CHOICES,
        default="ativo"
    )

    tipo_roteiro = models.CharField(
        "Tipo do Roteiro",
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        default="A"
    )
    revisao = models.PositiveIntegerField(
            "Revisão do Roteiro", blank=True,
        null=True
        )
    peso_unitario_gramas = models.DecimalField(
        "Peso Unitário (g)",
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    observacoes_gerais = CKEditor5Field(
            "Observações Gerais",
            config_name="default",
            blank=True,
            null=True
        )
    fontes_homologadas = models.ManyToManyField(FornecedorQualificado, blank=True, verbose_name="Fontes Homologadas")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    aprovado = models.BooleanField(
            "Aprovado?", default=False
        )
    aprovado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roteiros_aprovados",
        verbose_name="Aprovado por"
    )
    aprovado_em = models.DateTimeField(
        "Data de aprovação", null=True, blank=True
    )
    class Meta:
        verbose_name = "Roteiro de Produção"
        verbose_name_plural = "Roteiros de Produção"
    
    def __str__(self):
        tipo_display = self.get_tipo_roteiro_display()
        qtde_etapas = self.etapas.count()
        return f"{self.item.codigo} {tipo_display} ({qtde_etapas} etapa{'s' if qtde_etapas != 1 else ''})"



class EtapaRoteiro(models.Model):
    roteiro = models.ForeignKey(RoteiroProducao, on_delete=models.CASCADE, related_name="etapas")
    etapa = models.PositiveIntegerField("Etapa Nº")
    setor = models.ForeignKey(CentroDeCusto, on_delete=models.PROTECT)
    pph = models.DecimalField("Peças por Hora", max_digits=10, decimal_places=4, blank=True, null=True)
    setup_minutos = models.DecimalField("Tempo de Setup (min)", max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["etapa"]

    def __str__(self):
        return f"{self.roteiro.item.codigo} - Etapa {self.etapa}"


class PropriedadesEtapa(models.Model):
    etapa = models.OneToOneField(EtapaRoteiro, on_delete=models.CASCADE, related_name="propriedades")
    nome_acao = models.CharField("Nome da Ação", max_length=100)
    descricao_detalhada = models.TextField("Descrição Detalhada")
    maquinas = models.ManyToManyField(Maquina, blank=True, verbose_name="Máquinas Permitidas")
    ferramenta = models.ForeignKey(
            Ferramenta,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            verbose_name="Ferramenta"
        )

    seguranca_mp = models.BooleanField("MP", default=False)
    seguranca_ts = models.BooleanField("TS", default=False)
    seguranca_m1 = models.BooleanField("M1", default=False)
    seguranca_l1 = models.BooleanField("L1", default=False)
    seguranca_l2 = models.BooleanField("L2", default=False)
    
    def __str__(self):
        return f"Ação: {self.nome_acao}"


class InsumoEtapa(models.Model):
    etapa = models.ForeignKey('EtapaRoteiro', related_name="insumos", on_delete=models.CASCADE)
    materia_prima = models.ForeignKey("qualidade_fornecimento.MateriaPrimaCatalogo", on_delete=models.PROTECT)
    tipo_insumo = models.CharField(
        max_length=20,
        choices=[
            ("matéria_prima", "Matéria-Prima"),
            ("componente", "Componente"),
            ("insumos", "Insumos"),
            ("outros", "Outros"),
        ]
    )
    obrigatorio = models.BooleanField(default=False)

    desenvolvido = models.DecimalField("Desenvolvido em (mm)", max_digits=10, decimal_places=7, null=True, blank=True)
    peso_liquido = models.DecimalField("Peso Líquido (kg)", max_digits=10, decimal_places=7, null=True, blank=True)
    peso_bruto = models.DecimalField("Peso Bruto (kg)", max_digits=10, decimal_places=7, null=True, blank=True)

    def __str__(self):
        return f"{self.materia_prima.codigo} ({'obrigatório' if self.obrigatorio else 'opcional'})"
    

# tecnico/models/roteiro.py  (adicione abaixo das classes existentes)
from django.utils import timezone
from django.contrib.auth import get_user_model

class RoteiroRevisao(models.Model):
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    ]

    roteiro = models.ForeignKey(
        RoteiroProducao,
        related_name="revisoes",
        on_delete=models.CASCADE,
        verbose_name="Roteiro"
    )
    numero_revisao = models.CharField("Número da Revisão", max_length=20)
    data_revisao = models.DateField("Data da Revisão", default=timezone.now)
    descricao_mudanca = models.TextField("Descrição da Mudança", blank=True, null=True)
    status = models.CharField("Status da Revisão", max_length=10, choices=STATUS_CHOICES, default="ativo")
    criado_por = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-data_revisao", "-id"]

    def __str__(self):
        return f"Rev. {self.numero_revisao} — {self.roteiro}"
