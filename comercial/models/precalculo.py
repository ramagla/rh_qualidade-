# comercial/models/precalculo.py

from django.db import models
from django.contrib.auth import get_user_model
from comercial.models import Cotacao
from .item import Item
from django_ckeditor_5.fields import CKEditor5Field
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from decimal import Decimal

from .clientes import Cliente
from .centro_custo import CentroDeCusto
from tecnico.models.roteiro import InsumoEtapa, RoteiroProducao, EtapaRoteiro
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.ferramenta import Ferramenta
from .item import Item

User = get_user_model()

class AuditModel(models.Model):
    """Campos de auditoria / assinatura em todos os registros."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_created", verbose_name="Criado por"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_updated", verbose_name="Atualizado por"
    )

    class Meta:
        abstract = True


from decimal import Decimal

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from comercial.models import Cotacao
from django_ckeditor_5.fields import CKEditor5Field

User = get_user_model()

class PreCalculo(models.Model):
    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.CASCADE,
        related_name="precalculos"
    )
    numero = models.PositiveIntegerField("Número do Pré-Cálculo", editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    observacoes_materiais = CKEditor5Field(
        "Observações Materiais",
        config_name="default",
        blank=True,
        null=True
    )
    observacoes_servicos = CKEditor5Field(
        "Observações Serviços Externos",
        blank=True,
        null=True
    )
    preco_selecionado = models.DecimalField(
        "Preço Final Selecionado (R$)",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True
    )
    preco_manual = models.DecimalField(
        "Preço Final Manual (R$)",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True
    )

    def calcular_precos_sem_impostos(self):
        regras = getattr(self, "regras_calculo_item", None)
        if not regras:
            return []

        custos_diretos = sum(rot.custo_total for rot in self.roteiro_item.all())

        mat = self.materiais.filter(selecionado=True).first()
        materiais = (mat.peso_bruto or 0) * (mat.preco_kg or 0) if mat else 0

        servicos = sum(
            (s.peso_bruto or 0) * (s.preco_kg or 0)
            for s in self.servicos.all()
        )

        # 🚫 ferramentas removido
        base = custos_diretos + materiais + servicos

        impostos_basicos = base * (
            Decimal(regras.ir + regras.csll + regras.df + regras.dv) / 100
        )

        valores = []
        qtde = getattr(self.analise_comercial_item, "qtde_estimada", 1) or 1

        for margem in range(10, 61, 5):
            bruto = base + impostos_basicos
            total = bruto * (1 + Decimal(margem) / 100)
            unitario = total / Decimal(qtde)
            valores.append({
                "percentual": margem,
                "total": round(total, 2),
                "unitario": round(unitario, 4),
            })
        return valores


    class Meta:
        verbose_name = "Pré-Cálculo"
        verbose_name_plural = "Pré-Cálculos"
        unique_together = ("cotacao", "numero")

    def calcular_precos_com_impostos(self):
        regras = getattr(self, "regras_calculo_item", None)
        if not regras:
            return []

        custos_diretos = sum(rot.custo_total for rot in self.roteiro_item.all())

        mat = self.materiais.filter(selecionado=True).first()
        materiais = (mat.peso_bruto or 0) * (mat.preco_kg or 0) if mat else 0

        servicos = sum(
            (s.peso_bruto or 0) * (s.preco_kg or 0)
            for s in self.servicos.all()
        )

        # 🚫 ferramentas removido
        base = custos_diretos + materiais + servicos

        despesas = base * (Decimal(regras.df + regras.dv) / 100)
        impostos = base * Decimal(
            regras.icms + regras.pis + regras.confins +
            regras.ir + regras.csll + regras.df + regras.dv
        ) / 100

        valores = []
        qtde = getattr(self.analise_comercial_item, "qtde_estimada", 1) or 1

        for margem in range(10, 61, 5):
            bruto = base + despesas + impostos
            total = bruto * (1 + Decimal(margem) / 100)
            unitario = total / Decimal(qtde)
            valores.append({
                "percentual": margem,
                "total": round(total, 2),
                "unitario": round(unitario, 4),
            })
        return valores


    def opcoes_precos(self):
        """Combina todos os valores calculados para alimentar o <select>."""
        opcoes = []
        for item in self.calcular_precos_sem_impostos():
            opcoes.append({
                "descricao": f"{item['percentual']}% sem impostos",
                "valor": item["total"]
            })
        for item in self.calcular_precos_com_impostos():
            opcoes.append({
                "descricao": f"{item['percentual']}% com impostos",
                "valor": item["total"]
            })
        return opcoes

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = PreCalculo.objects.aggregate(
                models.Max("numero")
            )["numero__max"] or 0
            self.numero = ultimo + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pré-Cálculo #{self.numero} – Cotação #{self.cotacao.numero}"




class AnaliseComercial(models.Model):
    """Perguntas de análise comercial vinculadas à cotação."""    
    STATUS_CHOICES = [
        ("andamento", "Em Andamento"),
        ("aprovado", "Aprovado"),
        ("reprovado", "Reprovado"),
        ("amostras", "Solicitação de Amostras"),
    ]

    METODOLOGIA = [
        ("Não aplicável", "Não aplicável"),
        ("PPAP Nível 1", "PPAP Nível 1"),
        ("PPAP Nível 2", "PPAP Nível 2"),
        ("PPAP Nível 3", "PPAP Nível 3"),
        ("PPAP Nível 4", "PPAP Nível 4"),
        ("PPAP Nível 5", "PPAP Nível 5"),
    ]
    RESULTADO = [
        ("Viável", "Viavel (O produto pode ser produzido conforme especificado,sem revisoes) "),
        ("Viável c/ Recomendações", "Viável (alterações recomendadas conforme considerações)"),
        ("Inviável", "Inviável (necessidade de revisão do projeto para a manufatura do produto dentro dos requisitos especificados)"),
    ]

    PERIODICIDADE = [
        ("Único", "Único"),
        ("Quinzenal", "Quinzenal"),
        ("Mensal", "Mensal"),
        ("Trimestral", "Trimestral"),
        ("Semestral", "Semestral"),
        ("Anual", "Anual"),
        ("Esporádico", "Esporádico"),
    ]
    precalculo = models.OneToOneField("PreCalculo", on_delete=models.CASCADE, related_name="analise_comercial_item", null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name="Selecione o item")

    metodologia = models.CharField("Metodologia de Aprovação", max_length=30, choices=METODOLOGIA)

    material_fornecido = models.BooleanField("2. Material fornecido pelo cliente ?", default=False)
    material_fornecido_obs = models.CharField("Detalhar Material", max_length=200, blank=True)

    requisitos_entrega = models.BooleanField("3. Existe Requisitos de Entrega (frequência)?", default=False)
    requisitos_entrega_obs = models.CharField("Detalhar Entrega", max_length=200, blank=True)

    requisitos_pos_entrega = models.BooleanField("4. Existe Requisitos Pós-Entrega ?", default=False)
    requisitos_pos_entrega_obs = models.CharField("Detalhar Pós-Entrega", max_length=200, blank=True)

    requisitos_comunicacao = models.BooleanField("5. Existe requisito de Comunicação Eletrônica com o cliente?", default=False)
    requisitos_comunicacao_obs = models.CharField("Detalhar Comunicação", max_length=200, blank=True)

    requisitos_notificacao = models.BooleanField("6. Existe requisito de notificação de Embarque ?", default=False)
    requisitos_notificacao_obs = models.CharField("Detalhar Notificação", max_length=200, blank=True)

    especificacao_embalagem = models.BooleanField("7. Existe especificação de Embalagem", default=False)
    especificacao_embalagem_obs = models.CharField("Detalhar Embalagem", max_length=200, blank=True)

    especificacao_identificacao = models.BooleanField("8. Existe especificação de Identificação", default=False)
    especificacao_identificacao_obs = models.CharField("Detalhar Identificação", max_length=200, blank=True)

    tipo_embalagem = models.BooleanField("9. Qual o tipo de embalagem a ser utilizada ?", default=False)
    tipo_embalagem_obs = models.CharField("Detalhar Tipo", max_length=200, blank=True)

    conclusao = models.CharField("Conclusão da Análise Crítica", max_length=30, choices=RESULTADO)
    consideracoes = CKEditor5Field("Considerações", config_name="default", blank=True, null=True)
    qtde_estimada = models.PositiveIntegerField("Quantidade Estimada", null=True, blank=True)

    # 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)
    periodo = models.CharField("Periodicidade de Fornecimento", max_length=20, choices=PERIODICIDADE, blank=True, null=True)
    status = models.CharField("Status da Análise", max_length=20, choices=STATUS_CHOICES, default="andamento")
    motivo_reprovacao = models.TextField("Motivo da Reprovação", blank=True, null=True)
    
    class Meta:
        verbose_name = "Análise Comercial"
        verbose_name_plural = "Análises Comerciais"

    def __str__(self):
        return f"Análise Comercial – Cotação #{self.precalculo.cotacao.numero}"


class PreCalculoMaterial(AuditModel):

    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Cotação'),
        ('ok', 'OK'),
    ]

    precalculo = models.ForeignKey("PreCalculo", on_delete=models.CASCADE, related_name="materiais", null=True, blank=True)
    roteiro = models.ForeignKey(RoteiroProducao, on_delete=models.PROTECT, verbose_name="Roteiro de Produção", null=True, blank=True)

    # Copiados do Roteiro/Insumo na criação
    nome_materia_prima = models.CharField("Nome da Matéria-prima", max_length=200, blank=True, null=True)
    codigo = models.CharField("Código", max_length=50)
    descricao = models.CharField("Descrição", max_length=300, blank=True, null=True)
    unidade = models.CharField("Unidade", max_length=20, blank=True, null=True)

    lote_minimo = models.PositiveIntegerField("Lote Mínimo", null=True, blank=True)
    entrega_dias = models.PositiveIntegerField("Entrega (dias)", null=True, blank=True)
    fornecedor = models.ForeignKey(FornecedorQualificado, on_delete=models.PROTECT, null=True, blank=True)
    icms = models.DecimalField("ICMS (%)", max_digits=5, decimal_places=2, null=True, blank=True)

    selecionado = models.BooleanField(default=False)

    desenvolvido_mm = models.DecimalField("Desenvolvido (mm)", max_digits=8, decimal_places=4)
    peso_liquido = models.DecimalField("Peso Líquido (kg)", max_digits=20, decimal_places=7)
    peso_bruto = models.DecimalField("Peso Bruto (kg)", max_digits=20, decimal_places=7)
    preco_kg = models.DecimalField("Preço /kg", max_digits=12, decimal_places=4, null=True, blank=True)

    status = models.CharField("Status da Cotação", max_length=20, choices=STATUS_CHOICES, default='aguardando')

    # 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Pré-Cálculo Matéria-Prima"
        verbose_name_plural = "Materiais Pré-Cálculo"



class PreCalculoServicoExterno(AuditModel):
    """Serviços externos do pré-cálculo, baseados em insumos de etapas com setor 'Tratamento Externo'."""

    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Cotação'),
        ('ok', 'OK'),
    ]

    precalculo = models.ForeignKey(
        "PreCalculo",
        on_delete=models.CASCADE,
        related_name="servicos",
        null=True, blank=True
    )

    insumo = models.ForeignKey(
        InsumoEtapa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Insumo (original do roteiro)"
    )

    nome_insumo = models.CharField("Nome do Insumo", max_length=200, blank=True, null=True)
    codigo_materia_prima = models.CharField("Código MP", max_length=50, blank=True, null=True)
    descricao_materia_prima = models.CharField("Descrição MP", max_length=300, blank=True, null=True)
    unidade = models.CharField("Unidade MP", max_length=20, blank=True, null=True)


    lote_minimo = models.PositiveIntegerField("Lote Mínimo", null=True, blank=True)
    entrega_dias = models.PositiveIntegerField("Entrega (dias)", null=True, blank=True)
    fornecedor = models.ForeignKey(
        FornecedorQualificado, on_delete=models.PROTECT,
        null=True, blank=True
    )
    icms = models.DecimalField(
        "ICMS (%)", max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    desenvolvido_mm = models.DecimalField("Desenvolvido (mm)", max_digits=8, decimal_places=2)
    peso_liquido = models.DecimalField("Peso Líquido (kg)", max_digits=20, decimal_places=7)
    peso_bruto = models.DecimalField("Peso Bruto (kg)", max_digits=20, decimal_places=7)
    preco_kg = models.DecimalField("Preço /kg", max_digits=12, decimal_places=4, null=True, blank=True)
    selecionado = models.BooleanField(default=False)

    status = models.CharField("Status da Cotação", max_length=20, choices=STATUS_CHOICES, default='aguardando')

    # 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Pré-Cálculo Serviço Externo"
        verbose_name_plural = "Serviços Externos Pré-Cálculo"

    def save(self, *args, **kwargs):
        if self.insumo and self.insumo.materia_prima:
            self.codigo = self.insumo.materia_prima.codigo
        super().save(*args, **kwargs)

    def __str__(self):
        try:
            return f"Serviço Externo - {self.insumo.materia_prima.codigo}"
        except Exception:
            return "Serviço Externo - sem código"

class AvaliacaoTecnica(AuditModel):
    RESULTADO = [
        ("Viável", "Viavel (O produto pode ser produzido conforme especificado,sem revisoes) "),
        ("Viável c/ Recomendações", "Viável (alterações recomendadas conforme considerações)"),
        ("Inviável", "Inviável (necessidade de revisão do projeto para a manufatura do produto dentro dos requisitos especificados)"),
    ]

    OPCOES_BOOL_EXTENDIDA = [
        (None, "Não aplicável"),
        (True, "Sim"),
        (False, "Não"),
    ]

    """Questionário de avaliação técnica na cotação."""
    precalculo = models.OneToOneField(
        "PreCalculo", on_delete=models.CASCADE,
        related_name="avaliacao_tecnica_item", null=True, blank=True
    )

    # 1. A empresa possui projeto próprio ou desenho fornecido?
    possui_projeto = models.BooleanField("1. Existe característica especoal além das relacionadas nas especificações ?", default=False)
    projeto_obs = models.CharField("Detalhes sobre o projeto/desenho", max_length=300, blank=True)

    # 2. É necessário desenvolvimento de dispositivo de controle?
    precisa_dispositivo = models.BooleanField("2. A peça é item de aparência ?", default=False)
    dispositivo_obs = models.CharField("Detalhes sobre o dispositivo", max_length=300, blank=True)

    # 3. Existem características críticas definidas?
    caracteristicas_criticas = models.BooleanField("3. O cliente forneceu FMEA de produto ?", default=False)
    criticas_obs = models.CharField("Quais são essas características?", max_length=300, blank=True)

    # 4. Existe necessidade de amostras para validação?
    precisa_amostras = models.BooleanField("4. O cliente solicitou algum teste além dos relacionados nas especificações ?", default=False)
    amostras_obs = models.CharField("Detalhes sobre as amostras", max_length=300, blank=True)

    # 5. Alguma restrição dimensional ou geométrica?
    restricao_dimensional = models.BooleanField("5. O cliente forneceu lista de fornecedores/materiais aprovados ?", default=False)
    restricao_obs = models.CharField("Descreva a restrição", max_length=300, blank=True)

    # 6. Existe requisito de acabamento superficial?
    acabamento_superficial = models.BooleanField("6 .As normas/especificações/requisitos estão disponiveis?", default=False)
    acabamento_obs = models.CharField("Descreva o acabamento", max_length=300, blank=True)

    # 7. Haverá validação metrológica?
    validacao_metrologica = models.BooleanField("7. São aplicaveis requisitos estatutários/regulamentares ?", default=False)
    metrologia_obs = models.CharField("Detalhes sobre a validação", max_length=300, blank=True)

    # 8. Há exigência de rastreabilidade técnica?
    rastreabilidade = models.BooleanField("8. Existem requisitos adicionais e/ou não declarados pelo cliente ?", default=False)
    rastreabilidade_obs = models.CharField("Detalhes da rastreabilidade", max_length=300, blank=True)

    metas_a = models.BooleanField("9a. Metas de qualidade (exemplo PPM) ?", default=False)
    metas_a_obs = models.CharField("Detalhes", max_length=300, blank=True)
    
    metas_b = models.BooleanField("9b. Metas de produtividade ?", default=False)
    metas_b_obs = models.CharField("Detalhes", max_length=300, blank=True)

    metas_c = models.BooleanField("9c. Metas de desempenho (exemplo: Cp, Cpk, etc.) ?", default=False)
    metas_c_obs = models.CharField("Detalhes", max_length=300, blank=True)

    metas_d = models.BooleanField("9d. Metas de funcionamento ?", default=False)
    metas_d_obs = models.CharField("Detalhes", max_length=300, blank=True)

    seguranca = models.BooleanField("10. Os requisitos sobre o item de segurança foram considerados ?", null=True, choices=OPCOES_BOOL_EXTENDIDA)
    seguranca_obs = models.CharField("Detalhes", max_length=300, blank=True)

    requisito_especifico = models.BooleanField("11. O cliente forneceu requisito especifico ?", null=True, choices=OPCOES_BOOL_EXTENDIDA)
    requisito_especifico_obs = models.CharField("Detalhes", max_length=300, blank=True)

    conclusao_tec = models.CharField("Conclusão da Análise Crítica", max_length=30, choices=RESULTADO)
    consideracoes_tec = models.TextField("Considerações", blank=True, null=True)

# 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Avaliação Técnica"
        verbose_name_plural = "Avaliações Técnicas"



class CotacaoFerramenta(AuditModel):
    """Ferramentas envolvidas na cotação."""
    precalculo = models.ForeignKey("PreCalculo", on_delete=models.CASCADE, related_name="ferramentas_item",null=True, blank=True)

    ferramenta = models.ForeignKey(
        Ferramenta, on_delete=models.PROTECT
    )
    observacoes = CKEditor5Field("Observações", config_name="default", blank=True, null=True)
# 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Ferramenta na Cotação"
        verbose_name_plural = "Ferramentas na Cotação"


class RegrasCalculo(AuditModel):
    """Impostos e encargos para o pré-cálculo."""
    precalculo = models.OneToOneField("PreCalculo", on_delete=models.CASCADE, related_name="regras_calculo_item",null=True, blank=True)

    icms = models.DecimalField("ICMS (%)", max_digits=5, decimal_places=2)
    pis = models.DecimalField("PIS (%)", max_digits=5, decimal_places=2)
    confins = models.DecimalField("Cofins (%)", max_digits=5, decimal_places=2)
    ir = models.DecimalField("IR (%)", max_digits=5, decimal_places=2)
    csll = models.DecimalField("CSLL (%)", max_digits=5, decimal_places=2)
    df = models.DecimalField("DF (%)", max_digits=5, decimal_places=2)
    dv = models.DecimalField("DV (%)", max_digits=5, decimal_places=2)

# 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Regras de Cálculo"
        verbose_name_plural = "Regras de Cálculo"


class RoteiroCotacao(AuditModel):
    """Cópia de dados do roteiro de produção para a cotação."""
    precalculo = models.ForeignKey("PreCalculo", on_delete=models.CASCADE, related_name="roteiro_item",null=True, blank=True)

    etapa = models.PositiveIntegerField("Etapa Nº")
    setor = models.ForeignKey(CentroDeCusto, on_delete=models.PROTECT)
    pph = models.DecimalField("Peças por Hora", max_digits=10, decimal_places=4)
    setup_minutos = models.PositiveIntegerField("Tempo de Setup (min)")
    custo_hora = models.DecimalField("Custo Hora", max_digits=12, decimal_places=4)
    custo_total = models.DecimalField("Custo Total", max_digits=14, decimal_places=4)

    # 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Roteiro na Cotação"
        verbose_name_plural = "Roteiros na Cotação"


class Desenvolvimento(AuditModel):
    """Modelo final de desenvolvimento da cotação."""
    precalculo = models.OneToOneField("PreCalculo", on_delete=models.CASCADE, related_name="desenvolvimento_item",null=True, blank=True)

    completo = models.BooleanField("Tudo preenchido corretamente?", default=False)
    consideracoes = CKEditor5Field("Considerações Finais", config_name="default", blank=True, null=True)
# 🔐 Metadados de Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)
    
    class Meta:
        verbose_name = "Desenvolvimento da Cotação"
        verbose_name_plural = "Desenvolvimentos da Cotação"
