from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time
from django.utils import timezone

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno
from django.db.models import Sum



class Inspecao10(models.Model):  
    DISPOSICAO_CHOICES = [
        ("Sucatear", "Sucatear"),
        ("Devolver", "Devolver"),
    ]

    numero_op = models.CharField("Nº OP", max_length=20, default="000000")
    codigo_brasmol = models.ForeignKey(
        MateriaPrimaCatalogo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"tipo": "Tratamento"},
        verbose_name="Código Bras-Mol"
    )    
    data = models.DateField("Data", default=timezone.now)
    fornecedor = models.ForeignKey(FornecedorQualificado, on_delete=models.CASCADE)
    
    hora_inicio = models.TimeField("Hora - Início", default=time(0, 0, 0))
    hora_fim = models.TimeField("Hora - Fim", default=time(0, 0, 0))
    tempo_gasto = models.DurationField("Tempo Gasto", blank=True, null=True)

    quantidade_total = models.PositiveIntegerField("Quantidade Total", default=0)
    quantidade_nok = models.PositiveIntegerField("Quantidade Não OK", default=0)
    status = models.CharField("Status", max_length=30, blank=True, editable=False)

    observacoes = models.TextField("Observações", blank=True)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    disposicao = models.CharField("Disposição", max_length=20, choices=DISPOSICAO_CHOICES, default="Sucatear")

    class Meta:
        verbose_name = "Inspeção 10"
        verbose_name_plural = "Inspeções 10"

  

    def save(self, *args, **kwargs):
        if self.hora_inicio and self.hora_fim:
            inicio = datetime.combine(self.data, self.hora_inicio)
            fim = datetime.combine(self.data, self.hora_fim)
            self.tempo_gasto = fim - inicio if fim > inicio else timedelta()

        self.status = "FALHA DE BANHO" if self.quantidade_nok > 0 else "OK"
        super().save(*args, **kwargs)

        if self.disposicao == "Devolver" and self.quantidade_nok > 0:
            devolucao_existente = DevolucaoServicoExterno.objects.filter(
                inspecao__numero_op=self.numero_op,
                inspecao__codigo_brasmol=self.codigo_brasmol,
                inspecao__fornecedor=self.fornecedor
            ).first()

            if devolucao_existente:
                servico = devolucao_existente.servico
                servico.quantidade_enviada = (
                    DevolucaoServicoExterno.objects
                    .filter(servico=servico)
                    .aggregate(total=Sum("quantidade"))["total"] or 0
                ) + self.quantidade_nok
                servico.save()

                DevolucaoServicoExterno.objects.create(
                    inspecao=self,
                    servico=servico,
                    quantidade=self.quantidade_nok
                )

            else:
                servico = ControleServicoExterno.objects.create(
                    pedido=f"DEV-{self.numero_op}",
                    op=int(self.numero_op.replace("OP", "").strip()) if self.numero_op.isdigit() else 0,
                    nota_fiscal="DEVOLUÇÃO AUTOMÁTICA",
                    fornecedor=self.fornecedor,
                    codigo_bm=self.codigo_brasmol,
                    quantidade_enviada=self.quantidade_nok,
                    data_envio=None,  # <<< NÃO preenche data_envio
                    observacao=f"Devolução iniciada via F223 - OP {self.numero_op}",
                    status2="Aguardando Envio"
                )
                DevolucaoServicoExterno.objects.create(
                    inspecao=self,
                    servico=servico,
                    quantidade=self.quantidade_nok
                )




from django.db import models
from django.utils import timezone
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno

from django.utils import timezone

class DevolucaoServicoExterno(models.Model):
    inspecao = models.OneToOneField(Inspecao10, on_delete=models.CASCADE)
    servico = models.ForeignKey(ControleServicoExterno, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # ✅ NOVO: data da baixa
    baixado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Devolução da OP {self.inspecao.numero_op}"
