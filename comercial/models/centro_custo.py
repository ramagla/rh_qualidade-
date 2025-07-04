from django.db import models
from Funcionario.models.departamentos import Departamentos
from django.utils import timezone

class CentroDeCusto(models.Model):
    nome = models.CharField("Centro de Custo", max_length=100)
    custo_atual = models.DecimalField("Custo do Setor", max_digits=12, decimal_places=2)
    vigencia = models.DateField("Início da Vigência")
    observacao = models.TextField("Observação", blank=True, null=True)  # ← CAMPO ADICIONADO
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"
        ordering = ["nome"] 
        
    def __str__(self):
        return f"{self.nome} – R$ {self.custo_atual}"

    @property
    def custo_vigente(self):
        hoje = timezone.now().date()
        if self.vigencia <= hoje:
            return self.custo_atual
        else:
            ultimo_historico = self.historico_custos.filter(alterado_em__lt=self.vigencia).order_by("-alterado_em").first()
            if ultimo_historico:
                return ultimo_historico.custo_anterior
            return None  # ou 0, se preferir exibir zero

    def save(self, *args, **kwargs):
        if self.pk:
            original = CentroDeCusto.objects.get(pk=self.pk)
            if original.custo_atual != self.custo_atual:
                HistoricoCustoCentroDeCusto.objects.create(
                    centro=self,
                    custo_anterior=original.custo_atual,
                    novo_custo=self.custo_atual,
                    alterado_em=timezone.now()
                )
        super().save(*args, **kwargs)


class HistoricoCustoCentroDeCusto(models.Model):
    centro = models.ForeignKey(CentroDeCusto, on_delete=models.CASCADE, related_name="historico_custos")
    custo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    novo_custo = models.DecimalField(max_digits=12, decimal_places=2)
    alterado_em = models.DateTimeField()

    class Meta:
        verbose_name = "Histórico de Custo"
        verbose_name_plural = "Históricos de Custo"
        ordering = ["-alterado_em"]

    def __str__(self):
        return f"{self.centro.departamento.sigla} | R$ {self.custo_anterior} → R$ {self.novo_custo} em {self.alterado_em.strftime('%d/%m/%Y')}"
