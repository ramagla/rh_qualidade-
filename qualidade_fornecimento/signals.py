from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import RelatorioF045
from alerts.models import AlertaUsuario, AlertaConfigurado

@receiver(post_save, sender=RelatorioF045)
def gerar_alerta_f045(sender, instance, created, **kwargs):
    if created:
        try:
            config = AlertaConfigurado.objects.get(tipo="F045_GERADO", ativo=True)
            destinatarios = set(config.usuarios.all())

            for grupo in config.grupos.all():
                destinatarios.update(grupo.user_set.all())

            for user in destinatarios:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo="📄 Novo Relatório F045 Gerado",
                    mensagem=f"O relatório F045 número {instance.nro_relatorio} foi gerado para {instance.material}.",
                )

        except AlertaConfigurado.DoesNotExist:
            pass  # Nenhuma configuração ativa
