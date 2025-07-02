from django import template
from babel.numbers import format_currency

register = template.Library()

@register.filter
def horas_formatadas(duracao_decimal):
    try:
        horas = int(duracao_decimal)
        minutos = int((duracao_decimal - horas) * 60)
        return f"{horas:02}:{minutos:02}"
    except:
        return "00:00"

@register.filter
def traduzir_mes(valor):
    mapa = {
        "Jan": "Jan", "Feb": "Fev", "Mar": "Mar", "Apr": "Abr", "May": "Mai",
        "Jun": "Jun", "Jul": "Jul", "Aug": "Ago", "Sep": "Set",
        "Oct": "Out", "Nov": "Nov", "Dec": "Dez"
    }
    try:
        partes = valor.split("/")
        mes = mapa.get(partes[0], partes[0])
        return f"{mes}/{partes[1]}"
    except:
        return valor


@register.filter
def br_currency(value):
    try:
        return format_currency(value or 0, 'BRL', locale='pt_BR')
    except:
        return "R$ 0,00"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def separador_milhar(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except:
        return valor
    
@register.filter
def extrair_mes_ano(valor):
    """
    Extrai o valor no formato YYYY-MM e transforma em MM/YYYY.
    Espera strings como '2025-01'.
    """
    try:
        partes = valor.split("-")
        return f"{partes[1]}/{partes[0]}"
    except:
        return valor


@register.filter
def get_range(start, end):
    """
    Gera um range de valores para usar em dropdowns (ex: anos).
    Exemplo: {{ 2023|get_range:2030 }} → [2023, ..., 2029]
    """
    try:
        return range(int(start), int(end))
    except:
        return []
