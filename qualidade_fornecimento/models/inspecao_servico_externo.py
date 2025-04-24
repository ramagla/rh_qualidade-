# qualidade_fornecimento/models/inspecao_servico_externo.py

from django.db import models
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno

class InspecaoServicoExterno(models.Model):
    servico = models.OneToOneField(ControleServicoExterno, on_delete=models.CASCADE, related_name='inspecao')
    certificado_numero = models.CharField(max_length=100)
    certificado_anexo = models.FileField(upload_to="certificados_servico_externo/", blank=True, null=True)

    inspecao_visual = models.CharField(max_length=10, choices=[('OK', 'OK'), ('NOK', 'NOK')])
    espessura_camada = models.CharField(max_length=10, choices=[('OK', 'OK'), ('NOK', 'NOK')])
    salt_spray = models.CharField(max_length=10, choices=[('OK', 'OK'), ('NOK', 'NOK')])

    aprovado_condicionalmente = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, null=True)
    
    pdf = models.FileField(upload_to="inspecao_servico_externo_pdfs/", blank=True, null=True)


    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def status_geral(self):
        if self.aprovado_condicionalmente:
            return "Aprovado Condicionalmente"
        elif all([
            self.inspecao_visual == "OK",
            self.espessura_camada == "OK",
            self.salt_spray == "OK"
        ]):
            return "Aprovado"
        else:
            return "Reprovado"

    def __str__(self):
        return f"Inspeção do Pedido {self.servico.pedido}"