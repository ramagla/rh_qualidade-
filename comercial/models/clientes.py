from django.db import models

class Cliente(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]
     
     
    razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18)  # 00.000.000/0000-00
    ie = models.CharField(max_length=50, blank=True, null=True)
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    cep = models.CharField(max_length=9)  # 00000-000
    uf = models.CharField(max_length=2)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    logotipo = models.ImageField(upload_to='logos_clientes/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo')

    # Transportadora
    transportadora_razao_social = models.CharField(max_length=255)
    transportadora_cnpj = models.CharField(max_length=18)
    transportadora_ie = models.CharField(max_length=50, blank=True, null=True)
    transportadora_endereco = models.CharField(max_length=255)
    transportadora_numero = models.CharField(max_length=10)
    transportadora_complemento = models.CharField(max_length=100, blank=True, null=True)
    transportadora_bairro = models.CharField(max_length=100)
    transportadora_cidade = models.CharField(max_length=100)
    transportadora_cep = models.CharField(max_length=9)
    transportadora_uf = models.CharField(max_length=2)
    transportadora_telefone = models.CharField(max_length=20, blank=True, null=True)
    coleta = models.BooleanField(default=False)    
    transportadora_email = models.EmailField(blank=True, null=True)
    
    # Novo Acordeon: Contato
    nome_contato = models.CharField(max_length=100, blank=True, null=True)
    email_contato = models.EmailField(blank=True, null=True)
    telefone_contato = models.CharField(max_length=20, blank=True, null=True)
    cargo_contato = models.CharField(max_length=100, blank=True, null=True)

    # Outros
    icms = models.DecimalField(max_digits=5, decimal_places=2)
    ipi = models.DecimalField(max_digits=5, decimal_places=2)
    cfop = models.CharField(max_length=10)
    cond_pagamento = models.CharField(max_length=100)
    cod_bm = models.CharField(max_length=50)
    observacao = models.TextField(blank=True, null=True)
    atualizado_em = models.DateTimeField(
            auto_now=True,
            verbose_name="Atualizado em"
        )
    
    TIPO_CHOICES = [
        ('Automotivo', 'Automotivo'),
        ('Não Automotivo', 'Não Automotivo'),
        ('Reposição', 'Reposição'),
    ]
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=True, null=True)
    def __str__(self):
        return self.razao_social


class ClienteDocumento(models.Model):
    TIPO_CHOICES = [
        ('Cartao IPI', 'Cartão IPI'),
        ('Alteracao de CNPJ', 'Alteração de CNPJ'),
        ('Outros', 'Outros'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    arquivo = models.FileField(upload_to='documentos_clientes/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cliente.razao_social} - {self.tipo}"
