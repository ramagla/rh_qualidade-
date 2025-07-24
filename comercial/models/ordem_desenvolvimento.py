# comercial/models/ordem_desenvolvimento.py

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from comercial.models import PreCalculo, Item, Cotacao, Cliente
from comercial.models.cotacao import AuditModel
from django_ckeditor_5.fields import CKEditor5Field

User = get_user_model()

class OrdemDesenvolvimento(AuditModel):
    # ————————— Identificação —————————
    numero = models.PositiveIntegerField("Nº Ordem", unique=True, editable=False)
    precalculo = models.ForeignKey(PreCalculo, on_delete=models.PROTECT, verbose_name="Pré-Cálculo")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name="Item")
    email_ppap = models.EmailField("E-mail para envio PPAP", blank=True, null=True)
    codigo_brasmol = models.CharField("Código Bras-Mol", max_length=50, blank=True, null=True)
    prazo_solicitado = models.DateField("Prazo solicitado", blank=True, null=True)
    qtde_amostra = models.PositiveIntegerField("Quantidade de amostra", blank=True, null=True)

    RAZOES = [
        ("novo", "Novo item"), ("discrepancia", "Correção de discrepância"),
        ("transferencia", "Transferência para outro cliente"),
        ("especificacao", "Alteração de especificação"),
        ("fornecedor", "Alteração de fornecedor"),
        ("revalidacao", "Atualização/Revalidação"),
        ("ferramental", "Alteração de ferramental"),
        ("processo", "Alteração de processo"),
        ("amostras", "Amostras"),
    ]
    razao = models.CharField("Razão do desenvolvimento", max_length=30, choices=RAZOES)

    # ————————— Dados carregados automaticamente —————————
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    automotivo_oem = models.BooleanField("Automotivo OEM", default=False)
    comprador = models.CharField("Comprador", max_length=100, blank=True, null=True)
    requisito_especifico = models.BooleanField("Requisito Específico Cliente?", default=False)
    item_seguranca = models.BooleanField("É Item de Segurança?", default=False)
    codigo_desenho = models.CharField("Código do Desenho", max_length=50, blank=True, null=True)
    revisao = models.CharField("Revisão", max_length=10, blank=True, null=True)
    data_revisao = models.DateField("Data da Revisão", blank=True, null=True)
    metodologia_aprovacao = models.CharField("Metodologia de aprovação", max_length=30, blank=True, null=True)
    observacao = CKEditor5Field("Observações", config_name="default", blank=True, null=True)

    # ————————— Campos técnicos —————————
    FAMILIA_PRODUTO = [
        (x, x) for x in ["MCGC", "MTORGC", "HGD", "AGD", "MCGD", "MTORGX", "HGM", "AGE",
                         "MTRAGC", "MTORGD", "HGE", "PGC", "MTRAGX", "PEGE", "HGC",
                         "PGE", "MTRAGD", "PEGP", "AGC"]
    ]
    familia_produto = models.CharField("Família de Produto", max_length=20, choices=FAMILIA_PRODUTO, blank=True, null=True)

    USUAL_NOVO = [("usual", "Usual"), ("novo", "Novo")]
    SIM_NAO = [("sim", "Sim"), ("nao", "Não")]
    SIM_NAO_NA = [("sim", "Sim"), ("nao", "Não"), ("na", "N/A")]

    material = models.CharField("Material", max_length=10, choices=USUAL_NOVO, blank=True, null=True)
    revisar_pir = models.CharField("Revisar PIR?", max_length=3, choices=SIM_NAO, blank=True, null=True)
    aprovado = models.CharField("Aprovado?", max_length=5, choices=SIM_NAO_NA, blank=True, null=True)
    prazo_material = models.DateField("Prazo Material", blank=True, null=True)

    ROTINAS_SISTEMA = [("roteiro", "Roteiro de operações"), ("bloqueio", "Bloqueio"), ("na", "N/A")]
    rotinas_sistema = models.CharField("Rotinas do Sistema", max_length=20, choices=ROTINAS_SISTEMA, blank=True, null=True)
    prazo_rotinas = models.DateField("Prazo Rotinas", blank=True, null=True)

    DOCUMENTOS = [
        ("DB", "DB"), ("PC", "PC"), ("IP", "IP"), ("IRM", "IRM"),
        ("F048", "F048"), ("F049", "F049"), ("TB027", "TB027"), ("TB028", "TB028"),
        ("CAD", "CADASTRO DO DESENHO"), ("NA", "N/A"),
    ]
    documentos_producao = models.CharField("Documentos de produção", max_length=100, blank=True, null=True)
    prazo_docs = models.DateField("Prazo Documentos", blank=True, null=True)

    ferramenta = models.CharField("Ferramenta", max_length=3, choices=SIM_NAO, blank=True, null=True)
    tipo_ferramenta = models.CharField("Tipo Ferramenta", max_length=15, choices=[("nova", "Nova"), ("adaptacao", "Adaptação"), ("outros", "Outros")], blank=True, null=True)
    os_ferramenta = models.PositiveIntegerField("Nº OS Ferramenta", blank=True, null=True)
    prazo_ferramental = models.DateField("Prazo Ferramental", blank=True, null=True)

    dispositivo = models.CharField("Dispositivo", max_length=3, choices=SIM_NAO, blank=True, null=True)
    tipo_dispositivo = models.CharField("Tipo Dispositivo", max_length=15, choices=[("medicao", "Medição"), ("auxiliar", "Auxiliar")], blank=True, null=True)
    os_dispositivo = models.PositiveIntegerField("Nº OS Dispositivo", blank=True, null=True)
    prazo_dispositivo = models.DateField("Prazo Dispositivo", blank=True, null=True)

    amostra = models.CharField("Amostra", max_length=3, choices=SIM_NAO, blank=True, null=True)
    numero_op = models.PositiveIntegerField("Nº OP", blank=True, null=True)
    prazo_amostra = models.DateField("Prazo Amostra", blank=True, null=True)

    # Tratamentos externos
    tratamento_termico = models.CharField("Trat. térmico externo", max_length=3, choices=SIM_NAO, blank=True, null=True)
    tipo_tte = models.CharField("Tipo TTE", max_length=10, choices=USUAL_NOVO, blank=True, null=True)
    status_tte = models.CharField("Status TTE", max_length=10, choices=SIM_NAO_NA, blank=True, null=True)
    prazo_tte = models.DateField("Prazo TTE", blank=True, null=True)

    tratamento_superficial = models.CharField("Trat. superficial externo", max_length=3, choices=SIM_NAO, blank=True, null=True)
    tipo_tse = models.CharField("Tipo TSE", max_length=10, choices=USUAL_NOVO, blank=True, null=True)
    status_tse = models.CharField("Status TSE", max_length=10, choices=SIM_NAO_NA, blank=True, null=True)
    prazo_tse = models.DateField("Prazo TSE", blank=True, null=True)

    resistencia_corrosao = models.CharField("Resistência à corrosão", max_length=3, choices=SIM_NAO, blank=True, null=True)
    requisito_resistencia = models.CharField("Requisito resistência", max_length=255, blank=True, null=True)
    prazo_resistencia = models.DateField("Prazo resistência", blank=True, null=True)

    durabilidade = models.CharField("Durabilidade/Ciclagem", max_length=3, choices=SIM_NAO, blank=True, null=True)
    requisito_durabilidade = models.CharField("Requisito durabilidade",max_length=255, blank=True, null=True)
    prazo_durabilidade = models.DateField("Prazo durabilidade", blank=True, null=True)

    observacao_geral = CKEditor5Field("Observações gerais", config_name="default", blank=True, null=True)
    # Assinatura da Análise Comercial
    assinatura_comercial_nome = models.CharField("Assinatura Comercial – Nome", max_length=150, null=True, blank=True)
    assinatura_comercial_email = models.CharField("Assinatura Comercial – E-mail (CN)", max_length=150, null=True, blank=True)
    assinatura_comercial_data = models.DateTimeField("Assinatura Comercial – Data", null=True, blank=True)

    # Assinatura da Avaliação Técnica
    assinatura_tecnica_nome = models.CharField("Assinatura Técnica – Nome", max_length=150, null=True, blank=True)
    assinatura_tecnica_email = models.CharField("Assinatura Técnica – E-mail (CN)", max_length=150, null=True, blank=True)
    assinatura_tecnica_data = models.DateTimeField("Assinatura Técnica – Data", null=True, blank=True)
    usuario_comercial = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="od_comercial")
    usuario_tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="od_tecnico")


    def save(self, *args, **kwargs):
        if not self.numero:
            ano_atual = timezone.now().year
            ultimo = (
                OrdemDesenvolvimento.objects
                .filter(created_at__year=ano_atual)
                .aggregate(models.Max("numero"))["numero__max"]
            )
            self.numero = (ultimo or 99) + 1  # começa em 100
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Ordem de Desenvolvimento #{self.numero}"
