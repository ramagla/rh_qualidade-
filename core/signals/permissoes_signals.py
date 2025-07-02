from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from core.constants.permissoes import CUSTOM_PERMISSOES



@receiver(post_migrate)
def criar_permissoes_customizadas(sender, **kwargs):
    """
    Cria permissões customizadas após a aplicação das migrações.
    """
    for app_label, model, codename, name in CUSTOM_PERMISSOES:
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={"name": name}
        )
        if not created and perm.name != name:
            perm.name = name
            perm.save()
