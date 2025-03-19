from django.db import models


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
