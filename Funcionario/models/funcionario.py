import os
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .cargo import Cargo
from .departamentos import Departamentos

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if arquivo and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


def renomear_curriculo(instance, filename):
    nome, extensao = os.path.splitext(filename)
    novo_nome = f"{slugify(instance.nome)}-{instance.numero_registro}{extensao}"
    return os.path.join("curriculos_funcionarios", novo_nome)

def renomear_certificado_ensino_medio(instance, filename):
    nome, extensao = os.path.splitext(filename)
    novo_nome = f"certificado-ensino-medio-{slugify(instance.nome)}-{instance.numero_registro}{extensao}"
    return os.path.join("certificados_ensino_medio", novo_nome)


def renomear_assinatura(instance, filename):
    nome, extensao = os.path.splitext(filename)
    novo_nome = f"assinatura-{slugify(instance.nome)}{extensao}"
    return os.path.join("assinaturas_funcionarios", novo_nome)


def renomear_foto(instance, filename):
    nome, extensao = os.path.splitext(filename)
    novo_nome = f"foto-{slugify(instance.nome)}-{instance.numero_registro}{extensao}"
    return os.path.join("fotos_funcionarios", novo_nome)

class Funcionario(models.Model):
    """
    Representa um colaborador da empresa com dados pessoais, funcionais e históricos de CIPA e Brigada.
    """

    STATUS_CHOICES = [("Ativo", "Ativo"), ("Inativo", "Inativo")]
    EXPERIENCIA_CHOICES = [
        ("Sim", "Sim, (Anexar Curriculum ou cópia da Carteira Profissional no prontuário)"),
        ("Não", "Não, (Justificar através da Avaliação Prática da Atividade, devidamente assinada)"),
    ]
    GENERO_CHOICES = [
        ("Masculino", "Masculino"),
        ("Feminino", "Feminino"),
        ("Outro", "Outro"),
        ("Não Informado", "Não Informado"),
    ]
    TAMANHO_CAMISA_CHOICES = [("PP", "PP"), ("P", "P"), ("M", "M"), ("G", "G"), ("GG", "GG"), ("XG", "XG"), ("XXG", "XXG")]
    TIPO_CHOICES = [("operacional", "Operacional"), ("administrativo", "Administrativo")]

    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="funcionario")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    cargo_inicial = models.ForeignKey(Cargo, related_name="cargo_inicial_funcionarios", on_delete=models.CASCADE, verbose_name="Cargo Inicial")
    cargo_atual = models.ForeignKey(Cargo, related_name="cargo_atual_funcionarios", on_delete=models.CASCADE, null=True, verbose_name="Cargo Atual")
    numero_registro = models.CharField(max_length=20, unique=True, verbose_name="Número de Registro")
    numero_registro_recibo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número do Registro para Recibo")
    local_trabalho = models.ForeignKey(Departamentos, verbose_name="Local de Trabalho", on_delete=models.SET_NULL, null=True, blank=True, related_name="funcionarios")
    data_integracao = models.DateField(blank=True, null=True, verbose_name="Data de Integração")
    responsavel = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="funcionarios_gerenciados", verbose_name="Responsável")
    cargo_responsavel = models.ForeignKey(Cargo, null=True, blank=True, on_delete=models.SET_NULL, related_name="responsaveis", verbose_name="Cargo do Responsável")
    escolaridade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Escolaridade")
    data_desligamento = models.DateField(null=True, blank=True, verbose_name="Data de Desligamento")
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, default="Não Informado", verbose_name="Gênero")
    experiencia_profissional = models.CharField(max_length=3, choices=EXPERIENCIA_CHOICES, default="Sim", verbose_name="Experiência Profissional")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    foto = models.ImageField(upload_to=renomear_foto, blank=True,null=True,verbose_name="Foto",validators=[MaxFileSizeValidator(5)],)
    assinatura_eletronica = models.ImageField(upload_to=renomear_assinatura, blank=True, null=True, verbose_name="Assinatura Eletrônica")
    curriculo = models.FileField(upload_to=renomear_curriculo, blank=True, null=True, verbose_name="Currículo",validators=[MaxFileSizeValidator(5)],)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Ativo", verbose_name="Status")
    formulario_f146 = models.FileField(upload_to=renomear_certificado_ensino_medio,blank=True, null=True,verbose_name="Certificado de Conclusão do Ensino Médio",validators=[MaxFileSizeValidator(5)],)
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    camisa = models.CharField(max_length=3, choices=TAMANHO_CAMISA_CHOICES, blank=True, null=True, verbose_name="Tamanho da Camisa")
    calcado = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Número do Calçado")

    representante_cipa = models.BooleanField(default=False, verbose_name="Representante CIPA")
    tipo_cipa = models.CharField(max_length=20, blank=True, null=True, choices=[("Titular", "Titular"), ("Suplente", "Suplente")], verbose_name="Tipo CIPA")
    ordem_cipa = models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, "1º"), (2, "2º"), (3, "3º"), (4, "4º")], verbose_name="Ordem na CIPA")
    tipo_representacao_cipa = models.CharField(max_length=20, blank=True, null=True, choices=[("Empregados", "Empregados"), ("Empregador", "Empregador")], verbose_name="Representação CIPA")
    vigencia_cipa = models.DateField(blank=True, null=True, verbose_name="Vigência CIPA")

    representante_brigada = models.BooleanField(default=False, verbose_name="Representante Brigada")
    vigencia_brigada = models.DateField(blank=True, null=True, verbose_name="Vigência Brigada")

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="operacional", verbose_name="Tipo do Colaborador")

    def save(self, *args, **kwargs):
        """
        Desativa CIPA ou Brigada caso a vigência esteja vencida.
        """
        today = timezone.now().date()
        if self.vigencia_cipa and self.vigencia_cipa < today:
            self.representante_cipa = False
        if self.vigencia_brigada and self.vigencia_brigada < today:
            self.representante_brigada = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    @property
    def primeiro_nome(self):
        """Retorna o primeiro nome do funcionário."""
        return self.nome.split(" ")[0] if self.nome else ""

    def atualizar_escolaridade(self):
        """
        Atualiza o campo escolaridade com base nos treinamentos concluídos do funcionário.
        """
        hierarchy = {
            "tecnico": 1,
            "graduacao": 2,
            "pos-graduacao": 3,
            "mestrado": 4,
            "doutorado": 5,
        }
        treinamentos_concluidos = self.treinamentos.filter(status="concluido").exclude(categoria="capacitacao")
        treinamento_mais_alto = None
        maior_nivel = 0

        for treinamento in treinamentos_concluidos:
            nivel = hierarchy.get(treinamento.categoria, 0)
            if nivel > maior_nivel:
                maior_nivel = nivel
                treinamento_mais_alto = treinamento

        self.escolaridade = treinamento_mais_alto.get_categoria_display() if treinamento_mais_alto else None
        self.save()

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "Funcionários"
