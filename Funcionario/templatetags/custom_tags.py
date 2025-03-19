from django import template

register = template.Library()


@register.filter
def has_permission(user, perm_name):
    """
    Verifica se o usuário possui a permissão especificada.
    """
    if user.is_authenticated:
        return user.has_perm(perm_name)
    return False
