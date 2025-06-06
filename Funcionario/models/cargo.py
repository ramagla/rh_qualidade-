from django.db import models
from django.utils import timezone
from Funcionario.models.departamentos import Departamentos

NIVEIS_HIERARQUIA = [
    (1, "Alta Direção / Conselho"),
    (2, "Diretoria"),
    (3, "Gerência Sênior"),
    (4, "Gerência Média"),
    (5, "Coordenação"),
    (6, "Supervisão"),
    (7, "Liderança Técnica"),
    (8, "Analista / Técnico"),
    (9, "Assistente / Auxiliar"),
    (10, "Operacional"),
]

class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    numero_dc = models.CharField(max_length=4)
    
    descricao_arquivo = models.FileField(upload_to="cargos/", blank=True, null=True)
    departamento = models.ForeignKey(
        Departamentos,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargos",
        verbose_name="Departamento"
    )

    # NOVO CAMPO DE NÍVEL HIERÁRQUICO
    nivel = models.PositiveSmallIntegerField(
            choices=NIVEIS_HIERARQUIA,
            verbose_name="Nível Hierárquico",
            help_text="1 = Mais alto (Direção), 10 = Mais baixo (Operacional)",
            default=10
        )
    # Campos de texto para responsabilidade e autoridade, educação, treinamento e experiência
    responsabilidade_atividade_primaria = models.TextField(
        verbose_name="Responsabilidade e Autoridade: (Atividade Primária)",
        blank=True,
        null=True,
    )
    responsabilidade_atividade_secundaria = models.TextField(
        verbose_name="Responsabilidade e Autoridade: (Atividade Secundária)",
        blank=True,
        null=True,
    )
    educacao_minima = models.TextField(
        verbose_name="Educação mínima", blank=True, null=True
    )
    treinamento_externo = models.TextField(
        verbose_name="Treinamento / Curso (Externo)", blank=True, null=True
    )
    treinamento_interno_minimo = models.TextField(
        verbose_name="Treinamento mínimo (interno)", blank=True, null=True
    )
    experiencia_minima = models.TextField(
        verbose_name="Experiência mínima", blank=True, null=True
    )
    # Relacionamento com o modelo Funcionario
    elaborador = models.ForeignKey(
        "Funcionario.Funcionario",  # Referência atrasada ao modelo Funcionario
        verbose_name="Elaborador",
        related_name="cargos_elaborados",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    elaborador_data = models.DateField(
        verbose_name="Data de Elaboração", default=timezone.now
    )
    aprovador = models.ForeignKey(
        "Funcionario.Funcionario",  # Referência atrasada ao modelo Funcionario
        verbose_name="Aprovador",
        related_name="cargos_aprovados",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    aprovador_data = models.DateField(
        verbose_name="Data de Aprovação", default=timezone.now
    )

    def __str__(self):
        return f"{self.nome} - DC N° {self.numero_dc.zfill(2)}"




class Revisao(models.Model):
    cargo = models.ForeignKey(Cargo, related_name="revisoes", on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=20)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.cargo.nome}"
