from django.db import models
from django.contrib.auth.models import User, Group


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

    ]

    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES, unique=True)
    usuarios = models.ManyToManyField(User, blank=True, related_name="alertas_configurados")
    grupos = models.ManyToManyField(Group, blank=True)
    ativo = models.BooleanField(default=True)

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

        }
        return nomes_exibicao.get(self.tipo, self.tipo)