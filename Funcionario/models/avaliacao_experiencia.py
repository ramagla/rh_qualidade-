from django.db import models
from django.utils import timezone
from datetime import timedelta
from .funcionario import Funcionario

class AvaliacaoExperiencia(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)    
    gerencia = models.CharField(max_length=100, blank=True, null=True)

    # Campos específicos para o questionário de experiência
    adaptacao_trabalho = models.IntegerField(null=True, blank=True)
    interesse = models.IntegerField(null=True, blank=True)
    relacionamento_social = models.IntegerField(null=True, blank=True)
    capacidade_aprendizagem = models.IntegerField(null=True, blank=True)

    # Observações e orientação
    observacoes = models.TextField(blank=True, null=True)
    orientacao = models.CharField(max_length=100, blank=True, null=True)

    @property
    def get_status_avaliacao(self):
        if self.orientacao == "Efetivar":
            return "😃 Efetivar"
        elif self.orientacao == "Encaminhar p/ Treinamento":
            return "😊 Treinamento"
        elif self.orientacao == "Desligar":
            return "😕 Desligar"
        return "Indeterminado"

    def get_status_prazo(self):
        hoje = timezone.now().date()
        data_limite = self.data_avaliacao + timedelta(days=30)
        return "Dentro do Prazo" if data_limite >= hoje else "Em Atraso"

    def __str__(self):
        return f"Avaliação de Experiência de {self.funcionario} em {self.data_avaliacao}"
