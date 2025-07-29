from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from comercial.models import PreCalculo, Cliente
from django.contrib.auth import get_user_model

User = get_user_model()

class ViabilidadeAnaliseRisco(models.Model):
    numero = models.PositiveIntegerField("Nº Viabilidade", unique=True, editable=False)
    precalculo = models.OneToOneField(PreCalculo, on_delete=models.PROTECT, related_name="viabilidade_risco")

    # --- Dados do Cliente e Item (via PreCalculo e Item) ---
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    requisito_especifico = models.BooleanField("Requisito Específico Cliente?", default=False)
    automotivo_oem = models.BooleanField("Automotivo OEM?", default=False)
    item_seguranca = models.BooleanField("É Item de Segurança?", default=False)
    codigo_desenho = models.CharField("Código do Desenho", max_length=100, blank=True, null=True)
    revisao = models.CharField("Revisão", max_length=10, blank=True, null=True)
    data_desenho = models.DateField("Data do Desenho", blank=True, null=True)
    codigo_brasmol = models.CharField("Código Bras-Mol", max_length=50, blank=True, null=True)

    # --- Análise Comercial ---
    produto_definido = models.BooleanField(
        "O produto está devidamente definido (incluindo requisitos de aplicação, etc.) possibilitando a avaliação da viabilidade?",
        default=False
    )
    risco_comercial = models.BooleanField(
        "Existe algum risco comercial relevante aplicável a este produto e respectivo fornecimento, além do item apresentado acima?",
        default=False
    )

    assinatura_comercial_nome = models.CharField("Responsável Comercial – Nome", max_length=150, blank=True, null=True)
    assinatura_comercial_departamento = models.CharField("Departamento", max_length=50, default="COMERCIAL", blank=True, null=True)
    assinatura_comercial_data = models.DateTimeField(blank=True, null=True)

    conclusao_comercial = models.CharField(
        "Conclusão Comercial",
        max_length=30,
        choices=[("viavel", "Viável"), ("alteracoes", "Viável com alterações"), ("inviavel", "Inviável")]
    )
    consideracoes_comercial = CKEditor5Field("Considerações Comerciais", blank=True, null=True)

    # --- Análise de Custos ---
    capacidade_fabricacao = models.BooleanField("Existe capacidade adequada para fabricação?", default=False)
    custo_transformacao = models.BooleanField("Custo com equipamentos de transformação?", default=False)
    custo_ferramental = models.BooleanField("Custo com ferramental?", default=False)
    metodo_alternativo = models.BooleanField("Método alternativo de manufatura?", default=False)
    risco_logistico = models.BooleanField("Risco logístico relevante?", default=False)

    conclusao_custos = models.CharField(
        "Conclusão Custos",
        max_length=30,
        choices=[("viavel", "Viável"), ("alteracoes", "Viável com alterações"), ("inviavel", "Inviável")]
    )
    consideracoes_custos = CKEditor5Field("Considerações de Custos", blank=True, null=True)
    responsavel_custos = models.CharField("Responsável Custos", max_length=150, blank=True, null=True)
    departamento_custos = models.CharField("Departamento", max_length=100, default="CUSTOS")
    data_custos = models.DateTimeField(blank=True, null=True)

    # --- Análise Técnica ---
    recursos_suficientes = models.BooleanField("Recursos suficientes para manufatura?", default=False)
    atende_especificacoes = models.BooleanField("Especificações de engenharia atendidas?", default=False)
    atende_tolerancias = models.BooleanField("Pode ser fabricado conforme desenho?", default=False)
    capacidade_processo = models.BooleanField("Capacidade do processo é suficiente?", default=False)
    permite_manuseio = models.BooleanField("Permite técnicas eficientes de manuseio?", default=False)
    precisa_cep = models.BooleanField("Necessário controle estatístico do processo (CEP)?", default=False)
    cep_usado_similares = models.BooleanField("CEP já usado em similares?", default=False)
    processos_estaveis = models.BooleanField("Processos estão sob controle?", default=False)
    capabilidade_ok = models.BooleanField("Capabilidade atende requisitos?", default=False)
    atende_requisito_cliente = models.BooleanField("Atende requisito específico do cliente?", default=False)
    risco_tecnico = models.BooleanField("Risco técnico relevante?", default=False)

    conclusao_tecnica = models.CharField(
        "Conclusão Técnica",
        max_length=30,
        choices=[("viavel", "Viável"), ("alteracoes", "Viável com alterações"), ("inviavel", "Inviável")]
    )
    consideracoes_tecnicas = CKEditor5Field("Considerações Técnicas", blank=True, null=True)
    responsavel_tecnica = models.CharField("Responsável Técnico", max_length=150, blank=True, null=True)
    departamento_tecnica = models.CharField("Departamento", max_length=100, default="TÉCNICO")
    data_tecnica = models.DateTimeField(blank=True, null=True)

    # --- Metadados ---
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = ViabilidadeAnaliseRisco.objects.aggregate(models.Max("numero"))["numero__max"] or 99
            self.numero = ultimo + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Viabilidade #{self.numero}"
