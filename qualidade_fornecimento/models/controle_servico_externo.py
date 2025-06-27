from datetime import timedelta
from django.utils import timezone 

from django.db import models




class ControleServicoExterno(models.Model):
    pedido = models.CharField(max_length=100)
    op = models.PositiveIntegerField(
        verbose_name="Ordem de Produção"
    )  # <-- ADICIONADO AQUI
    nota_fiscal = models.CharField(
        max_length=100, verbose_name="Nota Fiscal"
    )  # <-- NOVO
    fornecedor = models.ForeignKey(
    "qualidade_fornecimento.FornecedorQualificado",
    on_delete=models.PROTECT,
    related_name="servicos_externos",
    )

    codigo_bm = models.ForeignKey(
    "qualidade_fornecimento.MateriaPrimaCatalogo",
    on_delete=models.PROTECT,
    limit_choices_to={"tipo": "Tratamento"},
    )
    quantidade_enviada = models.DecimalField(max_digits=10, decimal_places=2)
    data_envio = models.DateField(null=True, blank=True)
    data_retorno = models.DateField(null=True, blank=True)
    status2 = models.CharField(max_length=50, blank=True)    
    atraso_em_dias = models.IntegerField(null=True, blank=True)
    ip = models.IntegerField(null=True, blank=True)
    observacao = models.TextField(blank=True)
    lead_time = models.PositiveIntegerField(null=True, blank=True)
    previsao_entrega = models.DateField(null=True, blank=True)  # ✅ novo campo
    data_negociada = models.DateField("Data Negociada", null=True, blank=True)  # ✅ novo campo

    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    def calcular_total(self):
        total_dias = sum(ret.quantidade for ret in self.retornos.all())
        return self.quantidade_enviada - total_dias

    def calcular_status2(self):
        total = self.calcular_total()
        if total > 0:
            return "Atenção Saldo"
        elif total == 0:
            return "OK"
        else:
            return "Saldo maior que o enviado"

    def calcular_prev_entrega(self):
        if self.data_envio and self.lead_time:
            return self.data_envio + timedelta(days=self.lead_time)
        return None


    def calcular_atraso_em_dias(self):
        base_entrega = self.data_negociada or self.calcular_prev_entrega()
        if not base_entrega or not self.data_retorno:
            return 0
        atraso = (self.data_retorno - base_entrega).days
        return max(atraso, 0)  # 🔒 Garante que não seja negativo


    def calcular_ip(self):
        atraso = self.calcular_atraso_em_dias()
        if atraso >= 21:
            return 30
        elif atraso >= 16:
            return 20
        elif atraso >= 11:
            return 15
        elif atraso >= 7:
            return 10
        elif atraso >= 4:
            return 5
        elif atraso >= 1:
            return 2
        return 0
    
    def save(self, *args, **kwargs):
        from qualidade_fornecimento.models.inspecao10 import DevolucaoServicoExterno
    # Detecta se está sendo preenchido agora (só dispara se era nulo antes)
        envio_confirmado = (
            self.pk and
            self.data_envio and
            not ControleServicoExterno.objects.filter(pk=self.pk, data_envio__isnull=False).exists()
        )

        # Calcula os campos auxiliares
        self.previsao_entrega = self.calcular_prev_entrega()
        self.atraso_em_dias = self.calcular_atraso_em_dias()
        self.ip = self.calcular_ip()

        # Salva normalmente
        super().save(*args, **kwargs)

        # ⚠️ Executa a baixa no estoque apenas uma vez quando data_envio for preenchida
        if envio_confirmado:
            devolucoes = DevolucaoServicoExterno.objects.filter(servico=self)

            for devolucao in devolucoes:
                # Aqui é onde ocorre a "baixa" — você pode adicionar mais lógica se quiser
                devolucao.baixado_em = timezone.now()
                devolucao.save(update_fields=["baixado_em"])

            print(f"✅ Baixa realizada: {devolucoes.count()} devoluções da OP {self.op}")


        def __str__(self):
            return f"Pedido {self.pedido}"


class RetornoDiario(models.Model):
    servico = models.ForeignKey(
        ControleServicoExterno, on_delete=models.CASCADE, related_name="retornos"
    )
    data = models.DateField()
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.data} - {self.quantidade}"
