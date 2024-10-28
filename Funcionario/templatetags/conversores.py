from django import template

register = template.Library()

@register.filter
def horas_formatadas(duracao_decimal):
    horas = int(duracao_decimal)
    minutos = int((duracao_decimal - horas) * 60)
    return f"{horas:02}:{minutos:02}"
