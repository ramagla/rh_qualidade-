from django.db import models

class Cliente(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
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
    ]

    # Campos obrigatórios
    razao_social = models.CharField(max_length=255)
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
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logotipo = models.ImageField(upload_to='logos_clientes/', blank=True, null=True)
    coleta = models.BooleanField(default=False, verbose_name="Coleta")

    # Contato
    nome_contato = models.CharField(max_length=100, blank=True, null=True)
    email_contato = models.EmailField(blank=True, null=True)
    telefone_contato = models.CharField(max_length=20, blank=True, null=True)
    cargo_contato = models.CharField(max_length=100, blank=True, null=True)
    departamento_contato = models.CharField(max_length=100, blank=True, null=True)  # NOVO

    # Outros dados
    icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cfop = models.CharField(max_length=10, blank=True, null=True)
    cond_pagamento = models.CharField(max_length=100, blank=True, null=True)
    cod_bm = models.CharField(max_length=50, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.razao_social


from django.db import models
from .clientes import Cliente  # ajuste o import conforme sua estrutura se necessário

class ClienteDocumento(models.Model):
    TIPO_CHOICES = [
        ('Cartao IPI', 'Cartão IPI'),
        ('Alteracao de CNPJ', 'Alteração de CNPJ'),
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
