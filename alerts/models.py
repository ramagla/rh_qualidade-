from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


class Alerta(models.Model):
    ALERTA_CHOICES = [
        ("vencida", "Alerta de Calibração Vencida"),
        ("proxima", "Alerta de Calibração Próxima"),
    ]

    nome = models.CharField(
        max_length=100,
        unique=True,
        choices=ALERTA_CHOICES,
        verbose_name="Nome do Alerta",
    )
    descricao = models.TextField(verbose_name="Descrição do Alerta")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    destinatarios = models.TextField(
        # Campo para os e-mails
        verbose_name="Destinatários (e-mails separados por vírgula)"
    )

    def __str__(self):
        return self.nome

    def get_destinatarios_list(self):
        return [
            email.strip() for email in self.destinatarios.split(",") if email.strip()
        ]


class AlertaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alertas")
    titulo = models.CharField(max_length=120)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=50, blank=True, null=True)  # ← novo: tipo genérico
    referencia_id = models.PositiveIntegerField(blank=True, null=True)  # ← novo: ID do objeto
    url_destino = models.CharField(max_length=255, blank=True, null=True)  # ← novo: link no botão
    lido = models.BooleanField(default=False)
    excluido = models.BooleanField(default=False) 
    criado_em = models.DateTimeField(auto_now_add=True)

    exige_confirmacao = models.BooleanField(default=False)
    confirmado_em = models.DateTimeField(blank=True, null=True)
    def confirmar(self):
            self.lido = True
            self.confirmado_em = timezone.now()
            self.save(update_fields=["lido", "confirmado_em"])

    def __str__(self):
        return f"{self.titulo} → {self.usuario.username}"


class AlertaConfigurado(models.Model):
    TIPO_ALERTA_CHOICES = [
        ("F045_GERADO", "Geração de F045"),
        ("MANUTENCAO_PROXIMA", "Manutenção Próxima"),
        ("MANUTENCAO_VENCIDA", "Manutenção Vencida"),
        ("AVALIACAO_RISCO_PROXIMA", "Avaliação de Risco Próxima"),
        ("AUDITORIA_PROXIMA", "Auditoria Próxima"),
        ("CERTIFICACAO_PROXIMA", "Certificação Próxima"),
        ("PRECALCULO_GERADO", "📄 Pré-Cálculo Gerado"),
        ("AVALIACAO_TECNICA_PENDENTE", "🛠 Avaliação Técnica Pendente"),
        ("RESPOSTA_COTACAO_MATERIAL", "📦 Resposta de Cotação de Material"),
        ("RESPOSTA_COTACAO_SERVICO", "🛠 Resposta de Cotação de Serviço"),
        ("ROTEIRO_ATUALIZADO", "🧵 Roteiro Atualizado — Definir Preço Final"),  # ⬅️ NOVO
        ("SOLICITACAO_COTACAO_MATERIAL", "📨 Solicitação de Cotação de Material"),
        ("SOLICITACAO_COTACAO_SERVICO", "📨 Solicitação de Cotação de Serviço"),
        ("ORDEM_DESENVOLVIMENTO_CRIADA", "🆕 Nova Ordem de Desenvolvimento Criada"),
        ("VIABILIDADE_CRIADA", "🆕 Nova Viabilidade Criada"),



    ]

    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES, unique=True)
    usuarios = models.ManyToManyField(User, blank=True, related_name="alertas_configurados")
    grupos = models.ManyToManyField(Group, blank=True)
    ativo = models.BooleanField(default=True)
    exigir_confirmacao_modal = models.BooleanField(default=False)
    observacoes = models.TextField("Observações/Descrição", blank=True, null=True)

    def __str__(self):
        nomes_exibicao = {
            "F045_GERADO": "📄 Relatório F045 Gerado",
            "MANUTENCAO_PROXIMA": "🔧 Calibração (Dispositivo/Equipamento) Próxima",
            "MANUTENCAO_VENCIDA": "⚠️ Calibração (Dispositivo/Equipamento) Vencida",
            "AVALIACAO_RISCO_PROXIMA": "🛡️ Avaliação de Risco do Fornecedor Próxima",
            "AUDITORIA_PROXIMA": "📋 Auditoria de Fornecedor Próxima",
            "CERTIFICACAO_PROXIMA": "📜 Certificação de Fornecedor Próxima do Vencimento",
            "PRECALCULO_GERADO": "📄 Pré-Cálculo Gerado",
            "AVALIACAO_TECNICA_PENDENTE": "🛠 Avaliação Técnica Pendente",
            "RESPOSTA_COTACAO_MATERIAL": "📦 Resposta de Cotação de Material",
            "RESPOSTA_COTACAO_SERVICO": "🛠 Resposta de Cotação de Serviço",
            "ROTEIRO_ATUALIZADO": "🧵 Roteiro Atualizado — Definir Preço Final",  # Novo tipo
            "SOLICITACAO_COTACAO_MATERIAL": "📨 Solicitação de Cotação de Material",   # Novo tipo
            "SOLICITACAO_COTACAO_SERVICO": "📨 Solicitação de Cotação de Serviço",     # Novo tipo
            "ORDEM_DESENVOLVIMENTO_CRIADA": "🆕 Nova Ordem de Desenvolvimento Criada",
            "VIABILIDADE_CRIADA": "🆕 Nova Viabilidade Criada",

    


        }
        return nomes_exibicao.get(self.tipo, self.tipo)