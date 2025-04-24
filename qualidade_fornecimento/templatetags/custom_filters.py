from django import template
from datetime import timedelta


register = template.Library()

@register.filter
def dict_get(d, key):
    """Retorna d[key] se d for um dicionário; caso contrário, retorna uma string vazia."""
    if isinstance(d, dict):
        return d.get(key, "")
    return ""

@register.filter
def attr(obj, attr_name):
    """Retorna o atributo de um objeto cujo nome é passado como string."""
    try:
        return getattr(obj, attr_name)
    except Exception:
        return ""
@register.filter(name="get_dict_value")
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""

@register.filter
def add_attrs(field, attrs: str):
    """
    Adiciona múltiplos atributos HTML a um field do Django form.
    Ex: {{ field|add_attrs:"data-min=0.1,data-max=1.2" }}
    """
    final_attrs = {}
    for attr in attrs.split(","):
        key, val = attr.split("=")
        final_attrs[key.strip()] = val.strip()
    return field.as_widget(attrs=final_attrs)


register = template.Library()

@register.filter
def calc_peso_total(rolos):
    return sum([rolo.peso or 0 for rolo in rolos])


@register.filter
def add_days(date, days):
    try:
        return date + timedelta(days=int(days))
    except Exception:
        return date