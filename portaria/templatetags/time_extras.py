from datetime import datetime, timedelta
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


@register.filter
def formatar_timedelta(td):
    """
    Converte um timedelta (ex: DurationField) em string 'HH:MM'.
    Exibe corretamente valores negativos como '-01:15' ao invés de '-1 day, 22:45:00'.
    """
    if not isinstance(td, timedelta):
        return td

    total_seconds = td.total_seconds()
    negativo = total_seconds < 0
    total_seconds = abs(total_seconds)

    # Arredonda para o minuto mais próximo corretamente
    total_minutos = int((total_seconds + 30) // 60)

    horas = total_minutos // 60
    minutos = total_minutos % 60

    resultado = f"{horas:02d}:{minutos:02d}"
    return f"-{resultado}" if negativo else resultado
