# portaria/templatetags/time_extras.py
from django import template

register = template.Library()

@register.filter
def minutos_para_horas(minutos):
    try:
        minutos = int(round(minutos))
        horas = minutos // 60
        resto = minutos % 60
        return f"{horas:02d}:{resto:02d}"
    except:
        return "—"


@register.filter
def divmod_horas(total_minutos):
    try:
        total_minutos = int(float(total_minutos))
        horas, minutos = divmod(total_minutos, 60)
        return f"{horas:02}:{minutos:02}"
    except:
        return "00:00"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)