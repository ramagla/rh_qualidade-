from django import template
from babel.numbers import format_currency

register = template.Library()

@register.filter
def brl(value):
    """
    Formata número no padrão R$ 1.234,56
    """
    if value is None:
        return ""
    try:
        return format_currency(value, "BRL", locale="pt_BR")
    except:
        return value


@register.filter
def field_value(bound_field):
    try:
        return bound_field.value()
    except Exception:
        return None


@register.filter
def attr(form, field_name):
    """
    Acessa dinamicamente um campo do formulário (ex: form|attr:"meu_campo").
    """
    try:
        return form[field_name]
    except Exception:
        return None

@register.filter
def dict_get(form, key):
    """
    Acessa um campo de formulário dinamicamente, compatível com BoundField.
    """
    try:
        return form[key]
    except (KeyError, AttributeError, TypeError):
        return None