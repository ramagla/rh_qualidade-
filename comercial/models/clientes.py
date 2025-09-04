from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from rh_qualidade.utils import formatar_nome_atividade_com_siglas  # ajuste o caminho se necessário

class Cliente(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Reativado', 'Reativado'),
    ]


    TIPO_CHOICES = [
    ('Automotivo', 'Automotivo'),
    ('Não Automotivo', 'Não Automotivo'),
    ('Reposição', 'Reposição'),
    ('Transportadora', 'Transportadora'),    
    ]


    TIPO_CADASTRO_CHOICES = [
        ('Cliente', 'Cliente'),
        ('Transportadora', 'Transportadora'),
        ('Fornecedor', 'Fornecedor'),

    ]

    # Campos obrigatórios
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(max_length=18, unique=True)
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    cep = models.CharField(max_length=9)
    uf = models.CharField(max_length=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo')
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CHOICES)
    tipo_cadastro = models.CharField(max_length=20, choices=TIPO_CADASTRO_CHOICES, default='Cliente')
    transportadora = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_atendidos',
        limit_choices_to={'tipo_cadastro': 'Transportadora'},
        verbose_name="Transportadora"
    )
    
    # Campos opcionais
    ie = models.CharField(max_length=50, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logotipo = models.ImageField(upload_to='logos_clientes/', blank=True, null=True)
    coleta = models.BooleanField(default=False, verbose_name="Coleta")

    # Contato
    nome_contato = models.CharField(max_length=100, blank=True, null=True)
    email_contato = models.EmailField(blank=True, null=True)
    telefone_contato = models.CharField(max_length=100, blank=True, null=True)
    cargo_contato = models.CharField(max_length=100, blank=True, null=True)
    departamento_contato = models.CharField(max_length=100, blank=True, null=True)  # NOVO

    # Outros dados
    icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cfop = models.CharField(max_length=10, blank=True, null=True)
    cond_pagamento = models.CharField(max_length=100, blank=True, null=True)
    cod_bm = models.CharField(max_length=50, blank=True, null=True)
    observacao = CKEditor5Field("Particularidades do cliente", config_name="default", blank=True, null=True)
  # ✅ Novos campos de adimplência
    STATUS_ADIMPLENCIA_CHOICES = [
        ('Adimplente', 'Adimplente'),
        ('Inadimplente', 'Inadimplente'),
    ]
    status_adimplencia = models.CharField(
        max_length=20,
        choices=STATUS_ADIMPLENCIA_CHOICES,
        default='Adimplente',
        verbose_name="Status de Adimplência"
    )
    comprovante_adimplencia = models.FileField(
        upload_to='comprovantes_adimplencia/',
        blank=True,
        null=True,
        verbose_name="Comprovante de Adimplência (PDF)"
    )

    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def save(self, *args, **kwargs):
            # Padronização específica
            if self.nome_contato:
                self.nome_contato = formatar_nome_atividade_com_siglas(self.nome_contato)

            if self.cargo_contato:
                self.cargo_contato = formatar_nome_atividade_com_siglas(self.cargo_contato)

            if self.departamento_contato:
                self.departamento_contato = formatar_nome_atividade_com_siglas(self.departamento_contato)

            if self.cod_bm:
                self.cod_bm = self.cod_bm.upper()

            super().save(*args, **kwargs)
            
    def __str__(self):
        return self.razao_social


from django.db import models
from .clientes import Cliente  # ajuste o import conforme sua estrutura se necessário

class ClienteDocumento(models.Model):
    TIPO_CHOICES = [
        ('Cartao CNPJ', 'Cartão CNPJ'),
        ('Cartao de Inscrição Estadual/Municipal', 'Cartao de Inscrição Estadual/Municipal'),
        ('Carta IPI', 'Carta IPI'),
        ('Ficha Cadastral', 'Ficha Cadastral'),
        ('Cartão Suframa', 'Cartão Suframa'),
        ('Norma', 'Normas'),
        ('Outros', 'Outros'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        blank=True,
        null=True
    )
    arquivo = models.FileField(
        upload_to='documentos_clientes/',
        blank=True,
        null=True
    )
    data_upload = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.cliente.razao_social} - {self.tipo or 'Sem Tipo'}"
