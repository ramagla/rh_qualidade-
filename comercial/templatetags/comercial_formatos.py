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
