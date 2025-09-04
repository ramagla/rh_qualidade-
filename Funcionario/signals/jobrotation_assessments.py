# Funcionario/signals/jobrotation_signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from Funcionario.models.job_rotation_evaluation import JobRotationEvaluation
from Funcionario.models.jobrotation_assessments import (
    JobRotationAvaliacaoColaborador,
    JobRotationAvaliacaoGestor,
)

SITE_URL = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

def _montar_url(path: str) -> str:
    return f"{SITE_URL}{path}"

@receiver(post_save, sender=JobRotationEvaluation)
def criar_avaliacoes_e_disparar_links(sender, instance, created, **kwargs):
    """Quando avaliação RH ficar 'Apto', cria as avaliações de colaborador e gestor"""
    if instance.avaliacao_rh != "Apto":
        return

    # Colaborador
    col, _ = JobRotationAvaliacaoColaborador.objects.get_or_create(
        jobrotation=instance,
        defaults={
            "colaborador_nome": getattr(instance.funcionario, "nome", ""),
            "cargo_anterior": getattr(instance.cargo_atual, "nome", ""),
            "cargo_atual": getattr(instance.nova_funcao, "nome", "")
                          or getattr(instance.cargo_atual, "nome", ""),
            "setor_anterior": getattr(instance, "area", ""),
            "setor_atual": getattr(instance, "local_trabalho", ""),
        },
    )

    # Gestor
    ges, _ = JobRotationAvaliacaoGestor.objects.get_or_create(
        jobrotation=instance,
        defaults={
            "gestor_nome": getattr(instance.gestor_responsavel, "nome", ""),
            "gestor_cargo": getattr(getattr(instance.gestor_responsavel, "cargo_atual", None), "nome", ""),
            "gestor_setor": getattr(instance.gestor_responsavel, "local_trabalho", ""),
            "colaborador_treinado": True,
        },
    )

    # Emails
    if getattr(instance.funcionario, "email", None):
        url_c = _montar_url(f"/rh/jobrotation/avaliacoes/colaborador/{col.token_publico}/")
        send_mail(
            "Avaliação de Job Rotation (Colaborador)",
            f"Olá {instance.funcionario.nome},\nPreencha sua avaliação: {url_c}",
            settings.DEFAULT_FROM_EMAIL,
            [instance.funcionario.email],
            fail_silently=True,
        )

    if getattr(instance.gestor_responsavel, "email", None):
        url_g = _montar_url(f"/rh/jobrotation/avaliacoes/gestor/{ges.token_publico}/")
        send_mail(
            "Avaliação de Job Rotation (Gestor)",
            f"Olá {instance.gestor_responsavel.nome},\nPreencha sua avaliação: {url_g}",
            settings.DEFAULT_FROM_EMAIL,
            [instance.gestor_responsavel.email],
            fail_silently=True,
        )
