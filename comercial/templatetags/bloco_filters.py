from django import template

register = template.Library()

@register.filter
def peso_total_blocos(itens):
    try:
        return sum(i.peso_total for i in itens)
    except Exception:
        return 0
