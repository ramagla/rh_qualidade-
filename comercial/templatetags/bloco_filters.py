from django import template

register = template.Library()


@register.filter(name='peso_total_blocos')
def peso_total_blocos(itens):
    """
    Soma o peso_total de todos os itens passados (QuerySet ou lista).
    """
    try:
        return sum(getattr(i, "peso_total", 0) or 0 for i in itens)
    except Exception:
        return 0


@register.filter
def peso_material(itens, material):
    """
    Soma o peso_total de itens com material específico.
    """
    return sum(item.peso_total or 0 for item in itens if item.material == material)


@register.filter
def formato_brasileiro(value):
    """
    Formata número no padrão brasileiro com até 3 casas decimais, removendo zeros à direita.
    Exemplo: 10.386 → '10,386', 5.80 → '5,8'
    """
    if value is None:
        return ''
    try:
        valor = float(value)
        formatado = f"{valor:.3f}".rstrip('0').rstrip('.')
        return formatado.replace(".", ",")
    except (ValueError, TypeError):
        return value
