# portaria/templatetags/time_extras.py
from datetime import datetime
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


@register.filter
def diferenca_horas(inicio, fim):
    if not inicio or not fim:
        return "-"
    try:
        delta = datetime.combine(datetime.min, fim) - datetime.combine(datetime.min, inicio)
        total_minutos = delta.total_seconds() // 60
        horas = int(total_minutos // 60)
        minutos = int(total_minutos % 60)
        return f"{horas:02d}:{minutos:02d}"
    except Exception:
        return "-"