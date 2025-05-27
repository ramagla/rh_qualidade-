from django import template

register = template.Library()


@register.filter
def horas_formatadas(duracao_decimal):
    horas = int(duracao_decimal)
    minutos = int((duracao_decimal - horas) * 60)
    return f"{horas:02}:{minutos:02}"

@register.filter
def traduzir_mes(valor):
    mapa = {
        "Jan": "Jan", "Feb": "Fev", "Mar": "Mar", "Apr": "Abr", "May": "Mai",
        "Jun": "Jun", "Jul": "Jul", "Aug": "Ago", "Sep": "Set",
        "Oct": "Out", "Nov": "Nov", "Dec": "Dez"
    }
    partes = valor.split("/")
    mes = mapa.get(partes[0], partes[0])
    return f"{mes}/{partes[1]}"

