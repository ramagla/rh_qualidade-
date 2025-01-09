from django.db import models
from .funcionario import Funcionario

class AvaliacaoAnual(models.Model):
    data_avaliacao = models.DateField()
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    centro_custo = models.CharField(max_length=100, blank=True, null=True)
    
    # Campos do questionário
    postura_seg_trabalho = models.IntegerField(blank=True, null=True)
    qualidade_produtividade = models.IntegerField(blank=True, null=True)
    trabalho_em_equipe = models.IntegerField(blank=True, null=True)
    comprometimento = models.IntegerField(blank=True, null=True)
    disponibilidade_para_mudancas = models.IntegerField(blank=True, null=True)
    disciplina = models.IntegerField(blank=True, null=True)
    rendimento_sob_pressao = models.IntegerField(blank=True, null=True)
    proatividade = models.IntegerField(blank=True, null=True)
    comunicacao = models.IntegerField(blank=True, null=True)
    assiduidade = models.IntegerField(blank=True, null=True)
    avaliacao_global_avaliador = models.TextField(blank=True, null=True)
    avaliacao_global_avaliado = models.TextField(blank=True, null=True)

    def calcular_classificacao(self):
        total_pontos = (
            (self.postura_seg_trabalho or 0) + 
            (self.qualidade_produtividade or 0) + 
            (self.trabalho_em_equipe or 0) + 
            (self.comprometimento or 0) +
            (self.disponibilidade_para_mudancas or 0) + 
            (self.disciplina or 0) + 
            (self.rendimento_sob_pressao or 0) + 
            (self.proatividade or 0) + 
            (self.comunicacao or 0) + 
            (self.assiduidade or 0)
        )

        if total_pontos == 0:
            return {'percentual': 0, 'status': 'Indeterminado'}

        percentual = (total_pontos / 40) * 100  # Assume que o total máximo de pontos é 40
        status = ''

        if 25 <= percentual <= 45:
            status = 'Ruim'
        elif 46 <= percentual <= 65:
            status = 'Regular'
        elif 66 <= percentual <= 84:
            status = 'Bom'
        elif 85 <= percentual <= 100:
            status = 'Ótimo'

        return {'percentual': percentual, 'status': status}
    
    @staticmethod
    def get_status_text(value):
        status_map = {
            1: "Ruim",
            2: "Regular",
            3: "Bom",
            4: "Ótimo"
        }
        return status_map.get(value, "Indeterminado")
