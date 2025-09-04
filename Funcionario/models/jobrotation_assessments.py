# Funcionario/models/jobrotation_assessments.py
import uuid, hashlib, os
from django.db import models
from django.utils import timezone
from django.conf import settings

from .job_rotation_evaluation import JobRotationEvaluation  # já existe

SECRET_FIRMA = getattr(settings, "SIGNATURE_SECRET", "changeme-signature-secret")


class AssinaturaMixin(models.Model):
    # fluxo básico de assinatura
    assinante_nome   = models.CharField(max_length=150, blank=True, null=True)
    assinante_email  = models.EmailField(blank=True, null=True)
    assinado_em      = models.DateTimeField(blank=True, null=True)
    assinado_ip      = models.GenericIPAddressField(blank=True, null=True)
    assinado_hash    = models.CharField(max_length=64, blank=True, null=True)  # sha256
    assinado         = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _payload_para_hash(self) -> str:
        # junte aqui os campos relevantes para “congelar” o conteúdo da avaliação
        campos = []
        for f in self._meta.fields:
            if f.name in ["id", "token_publico", "assinado_hash", "assinado", "assinado_em",
                          "assinado_ip", "assinante_email", "assinante_nome", "created", "updated"]:
                continue
            valor = getattr(self, f.name)
            campos.append(f"{f.name}={valor}")
        return "|".join(campos) + f"|secret={SECRET_FIRMA}"

    def gerar_hash_assinatura(self):
        payload = self._payload_para_hash().encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def marcar_como_assinado(self, nome, email, ip=None):
        self.assinante_nome = nome
        self.assinante_email = email
        self.assinado_em = timezone.now()
        self.assinado_ip = ip
        self.assinado_hash = self.gerar_hash_assinatura()
        self.assinado = True


class JobRotationAvaliacaoColaborador(AssinaturaMixin):
    """Avaliação respondida pelo colaborador (etapa 1)."""
    token_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    jobrotation   = models.ForeignKey(JobRotationEvaluation, on_delete=models.CASCADE, related_name="avaliacoes_colaborador")

    # dados derivados / exibição
    colaborador_nome = models.CharField(max_length=150, blank=True, null=True)
    cargo_anterior   = models.CharField(max_length=150, blank=True, null=True)
    cargo_atual      = models.CharField(max_length=150, blank=True, null=True)
    setor_anterior   = models.CharField(max_length=150, blank=True, null=True)
    setor_atual      = models.CharField(max_length=150, blank=True, null=True)

    # — Perguntas —
    # 1
    p1_recebeu_infos             = models.BooleanField(default=False)
    p1_infos_foram               = models.CharField(max_length=20, choices=[("suficientes","suficientes"),("insuficientes","insuficientes")], blank=True, null=True)
    p1_faltaram                  = models.CharField(max_length=40, blank=True, null=True)  # "ordem técnica", "ordem administrativa"
    p1_favor_detalhar            = models.TextField(blank=True, null=True)
    # 2
    p2_teve_dificuldade          = models.BooleanField(default=False)
    p2_detalhes                  = models.TextField(blank=True, null=True)
    p2_adaptacao                 = models.CharField(max_length=10, choices=[("rápida","rápida"),("lenta","lenta"),("regular","regular")], blank=True, null=True)
    # 3
    p3_desempenho                = models.CharField(max_length=10, choices=[("ótimo","ótimo"),("bom","bom"),("regular","regular"),("ruim","ruim")], blank=True, null=True)
    # 4
    p4_atitude_duvida            = models.CharField(max_length=40, choices=[
        ("resolve sozinho","resolve sozinho"),
        ("solicita ajuda ao colega","solicita ajuda ao colega"),
        ("dirige-se ao chefe imediato","dirige-se ao chefe imediato"),
        ("nunca pede ajuda","nunca pede ajuda")
    ], blank=True, null=True)
    p4_como_e_atendido           = models.TextField(blank=True, null=True)
    # 5
    p5_metodo_empresa_ou_proprio = models.CharField(max_length=25, choices=[("método da empresa","método da empresa"),("próprio método","próprio método")], blank=True, null=True)
    p5_justifique                = models.TextField(blank=True, null=True)
    p5_houve_maior_rendimento    = models.BooleanField(default=False)
    # 6
    p6_dialogo_com_chefe         = models.BooleanField(default=True)
    p6_detalhar                  = models.TextField(blank=True, null=True)
    # 7
    p7_adaptou_facil             = models.TextField(blank=True, null=True)
    p7_adaptou_dificil           = models.TextField(blank=True, null=True)
    # 8
    p8_satisfeito                = models.BooleanField(default=True)
    p8_motivo_insatisfacao       = models.TextField(blank=True, null=True)
    # 9
    p9_como_adm_pessoal_ajuda    = models.TextField(blank=True, null=True)
    # 10
    p10_critica_sugestao         = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class JobRotationAvaliacaoGestor(AssinaturaMixin):
    """Avaliação respondida pelo gestor (etapa 2)."""
    token_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    jobrotation   = models.ForeignKey(JobRotationEvaluation, on_delete=models.CASCADE, related_name="avaliacoes_gestor")

    # cabeçalho
    gestor_nome   = models.CharField(max_length=150, blank=True, null=True)
    gestor_cargo  = models.CharField(max_length=150, blank=True, null=True)
    gestor_setor  = models.CharField(max_length=150, blank=True, null=True)
    colaborador_treinado = models.BooleanField(default=False)

    # — Perguntas —
    # 1
    g1_func_tinha_info     = models.BooleanField(default=False)
    g1_de_quem             = models.TextField(blank=True, null=True)
    g1_infos_foram         = models.CharField(max_length=20, choices=[("suficientes","suficientes"),("insuficientes","insuficientes")], blank=True, null=True)
    g1_faltaram            = models.CharField(max_length=40, blank=True, null=True)  # técnica/administrativa
    g1_detalhar            = models.TextField(blank=True, null=True)
    # 2
    g2_dificuldades        = models.BooleanField(default=False)
    g2_detalhar            = models.TextField(blank=True, null=True)
    g2_adaptacao           = models.CharField(max_length=10, choices=[("rápida","rápida"),("lenta","lenta"),("regular","regular")], blank=True, null=True)
    # 3
    g3_desempenho          = models.CharField(max_length=10, choices=[("ótimo","ótimo"),("bom","bom"),("regular","regular"),("ruim","ruim")], blank=True, null=True)
    # 4
    g4_atitude_duvida      = models.CharField(max_length=40, choices=[
        ("resolve sozinho","resolve sozinho"),
        ("solicita ajuda ao colega","solicita ajuda ao colega"),
        ("dirige-se ao chefe imediato","dirige-se ao chefe imediato"),
        ("nunca pede ajuda","nunca pede ajuda")
    ], blank=True, null=True)
    g4_como_e_atendido     = models.TextField(blank=True, null=True)
    # 5
    g5_cooperacao          = models.CharField(max_length=40, choices=[
        ("cooperação espontânea","cooperação espontânea"),
        ("não existe cooperação","não existe cooperação"),
        ("cooperação quando solicitado","cooperação quando solicitado"),
    ], blank=True, null=True)
    g5_justifique          = models.TextField(blank=True, null=True)
    # 6
    g6_treinamento_dialogo = models.BooleanField(default=True)
    g6_detalhar            = models.TextField(blank=True, null=True)
    # 7
    g7_adaptou_facil       = models.TextField(blank=True, null=True)
    g7_adaptou_dificil     = models.TextField(blank=True, null=True)
    # 8
    g8_satisfeito          = models.BooleanField(default=True)
    g8_motivo_insatisfacao = models.TextField(blank=True, null=True)
    # 9
    g9_como_adm_pessoal_ajuda = models.TextField(blank=True, null=True)
    # 10
    g10_critica_sugestao   = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
