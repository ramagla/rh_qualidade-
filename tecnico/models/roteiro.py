from django.db import models
from comercial.models.item import Item
from comercial.models.centro_custo import CentroDeCusto
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from tecnico.models.maquina import Maquina

from django_ckeditor_5.fields import CKEditor5Field
from comercial.models.ferramenta import Ferramenta  # no topo, se ainda não tiver

from django.db import models
from comercial.models.item import Item

class RoteiroProducao(models.Model):
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name="roteiro",
        verbose_name="Item"
    )

    massa_mil_pecas = models.DecimalField(
            "Massa por 1.000 peças (kg)",
            max_digits=10,
            decimal_places=2,
            blank=True,
            null=True
        )
    observacoes_gerais = CKEditor5Field(
            "Observações Gerais",
            config_name="default",
            blank=True,
            null=True
        )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Roteiro de Produção"
        verbose_name_plural = "Roteiros de Produção"
    
    def __str__(self):
        # se você quiser manter a contagem de etapas
        return f"Roteiro - {self.item.codigo} ({self.etapas.count()} etapas)"



class EtapaRoteiro(models.Model):
    roteiro = models.ForeignKey(RoteiroProducao, on_delete=models.CASCADE, related_name="etapas")
    etapa = models.PositiveIntegerField("Etapa Nº")
    setor = models.ForeignKey(CentroDeCusto, on_delete=models.PROTECT)
    pph = models.DecimalField("Peças por Hora", max_digits=10, decimal_places=4, blank=True, null=True)
    setup_minutos = models.PositiveIntegerField("Tempo de Setup (min)", blank=True, null=True)

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
    
    def __str__(self):
        return f"Ação: {self.nome_acao}"


class InsumoEtapa(models.Model):
    etapa = models.ForeignKey(EtapaRoteiro, related_name="insumos", on_delete=models.CASCADE)
    materia_prima = models.ForeignKey("qualidade_fornecimento.MateriaPrimaCatalogo", on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=6)
    tipo_insumo = models.CharField(max_length=20, choices=[("matéria_prima", "Matéria-Prima"), ("componente", "Componente"),("insumos", "Insumos"), ("outros", "Outros")])
    obrigatorio = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.insumo.codigo} ({'obrigatório' if self.obrigatorio else 'opcional'})"
