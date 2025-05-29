from django.db import models
from django.utils.timezone import now

from .funcionario import Funcionario
from Funcionario.models.departamentos import Departamentos


class Atividade(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome da Atividade")
    # Relacionado ao local_trabalho
    departamento = models.ForeignKey(
        Departamentos,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Departamento",
        related_name="atividades_departamento"
    )

    def __str__(self):
        return f"{self.nome} ({self.departamento})"


class Nota(models.Model):
    PONTUACAO_CHOICES = [
        (0, "Observador"),
        (1, "Aprendiz"),
        (2, "Assistente"),
        (3, "Autônomo"),
        (4, "Instrutor"),
    ]

    PERFIL_CHOICES = [
    ("suplente", "Suplente"),
    ("treinado", "Treinado"),
    ("em_treinamento", "Em Treinamento"),
    ("oficial", "Oficial"),
]

    SIM_NAO_CHOICES = [
        (True, "Sim"),
        (False, "Não"),
    ]

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.CASCADE, related_name="notas"
    )
    atividade = models.ForeignKey(
        Atividade, on_delete=models.CASCADE, related_name="notas"
    )
    pontuacao = models.PositiveSmallIntegerField(
        choices=PONTUACAO_CHOICES, verbose_name="Pontuação"
    )

    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        verbose_name="Perfil"
    )
    
    class Meta:
        unique_together = ("funcionario", "atividade")

    def __str__(self):
        return f"{self.funcionario.nome} - {self.atividade.nome}: {self.get_pontuacao_display()}"

    @staticmethod
    def get_notas_dict(atividades, funcionarios):
        notas = Nota.objects.filter(
            atividade__in=atividades, funcionario__in=funcionarios
        )
        notas_dict = {
            f"{nota.funcionario.id}_{nota.atividade.id}": nota.pontuacao
            for nota in notas
        }
        return notas_dict


class MatrizPolivalencia(models.Model):
    departamento = models.ForeignKey(
        Departamentos,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Departamento",
        related_name="matrizes_polivalencia"
    )
    elaboracao = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        related_name="elaboracao_matriz",
        verbose_name="Elaboração",
        blank=True,
        null=True,
    )
    coordenacao = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        related_name="coordenacao_matriz",
        verbose_name="Coordenação",
        blank=True,
        null=True,
    )
    validacao = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        related_name="validacao_matriz",
        verbose_name="Validação",
        blank=True,
        null=True,
    )
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return f"Matriz de Polivalência - {self.departamento or 'Sem Departamento'}"

    @property
    def atividades(self):
        # Retorna as atividades do departamento associado à matriz
        if self.departamento:
            return Atividade.objects.filter(departamento=self.departamento)
        return Atividade.objects.none()

    @property
    def funcionarios(self):
        # Filtra os funcionários com notas vinculadas às atividades deste departamento
        notas = Nota.objects.filter(atividade__departamento=self.departamento)
        funcionarios_ids = notas.values_list("funcionario_id", flat=True).distinct()
        return Funcionario.objects.filter(id__in=funcionarios_ids)

    @property
    def funcionarios_com_notas(self):
        # Retorna funcionários com notas vinculadas às atividades da matriz
        notas = Nota.objects.filter(atividade__in=self.atividades)
        funcionarios_ids = notas.values_list("funcionario_id", flat=True).distinct()
        return Funcionario.objects.filter(id__in=funcionarios_ids)

    def get_notas_por_funcionario(self):
        """
        Retorna um dicionário onde as chaves são IDs de funcionários e valores são dicionários de atividades e suas notas.
        """
        notas = Nota.objects.filter(atividade__in=self.atividades)
        notas_por_funcionario = {}
        for nota in notas:
            if nota.funcionario.id not in notas_por_funcionario:
                notas_por_funcionario[nota.funcionario.id] = {}
            notas_por_funcionario[nota.funcionario.id][
                nota.atividade.id
            ] = nota.pontuacao
        return notas_por_funcionario

    def delete(self, *args, **kwargs):
        # Exclui todas as notas relacionadas às atividades desta matriz
        Nota.objects.filter(atividade__departamento=self.departamento).delete()
        super().delete(*args, **kwargs)
