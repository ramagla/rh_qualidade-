from django import template

register = template.Library()


@register.filter
def get_dict_value(d, key):
    """Retorna o valor de um dicionário dado a chave."""
    return d.get(key, None)
