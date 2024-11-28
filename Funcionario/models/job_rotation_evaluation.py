from django.db import models
from .funcionario import Funcionario
from .cargo import Cargo

class JobRotationEvaluation(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="job_rotation_evaluations")
    local_trabalho = models.CharField(max_length=100, null=True, blank=True)
    cargo_atual = models.ForeignKey(Cargo, related_name='job_rotation_evaluations_cargo', on_delete=models.CASCADE, null=True, blank=True)
    competencias = models.TextField(null=True, blank=True)
    data_ultima_avaliacao = models.DateField(null=True, blank=True)
    status_ultima_avaliacao = models.CharField(max_length=50, null=True, blank=True)
    cursos_realizados = models.JSONField(default=list, null=True, blank=True)  # Lista de cursos realizados
    escolaridade = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100)
    nova_funcao = models.ForeignKey(Cargo, related_name='nova_funcao', on_delete=models.SET_NULL, null=True, blank=True)
    data_inicio = models.DateField()
    termino_previsto = models.DateField(editable=False, null=True, blank=True)
    gestor_responsavel = models.ForeignKey(Funcionario, related_name='gestor_responsavel', on_delete=models.SET_NULL, null=True)
    descricao_cargo = models.TextField(null=True, blank=True)
    treinamentos_requeridos = models.TextField(blank=True)
    treinamentos_propostos = models.TextField(blank=True)
    avaliacao_gestor = models.TextField(blank=True)
    avaliacao_funcionario = models.TextField(blank=True)
    avaliacao_rh = models.CharField(
        max_length=20,
        choices=[
            ('Apto', 'Apto'), 
            ('Inapto', 'Inapto'), 
            ('Prorrogar TN', 'Prorrogar TN'), 
            ('EmProgresso', 'Em Progresso')
        ],  # Adicionado "Em Progresso"
    )
    disponibilidade_vaga = models.BooleanField(default=False)

    def __str__(self):
        return f"Avaliação de Job Rotation - {self.funcionario.nome}"
