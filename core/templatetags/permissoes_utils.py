from django import template

register = template.Library()

@register.filter
def tem_permissao(usuario, perm_codename):
    """Verifica se o usuário possui permissão direta ou via grupo."""
    if usuario and perm_codename:
        return usuario.has_perm(perm_codename.strip())
    return False

@register.filter
def has_permission(user, perm):
    return user.has_perm(perm)

@register.filter
def traduz_perm(nome):
    """Traduz o nome de permissões padrão do Django para português."""
    if nome.startswith("Can add "):
        return "Adicionar " + nome.replace("Can add ", "").capitalize()
    if nome.startswith("Can change "):
        return "Editar " + nome.replace("Can change ", "").capitalize()
    if nome.startswith("Can delete "):
        return "Excluir " + nome.replace("Can delete ", "").capitalize()
    if nome.startswith("Can view "):
        return "Visualizar " + nome.replace("Can view ", "").capitalize()
    return nome
