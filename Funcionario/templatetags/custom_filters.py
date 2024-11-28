from django import template

register = template.Library()



@register.filter
def dict_get(d, key):
    try:
        return d.get(key, None)
    except AttributeError:
        return None



@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter
def get_nested_item(dictionary, keys):
    try:
        key1, key2 = keys.split(",")
        return dictionary.get(key1, {}).get(key2)
    except (ValueError, AttributeError):
        return None

@register.filter
def auto_breaks(value, max_length=20):
    """
    Quebra o texto dinamicamente a cada 'max_length' caracteres ou após palavras específicas.
    """
    words = value.split()  # Divide o texto em palavras
    lines = []
    current_line = ""

    for word in words:
        # Adiciona a palavra à linha atual, respeitando o limite de comprimento
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())  # Adiciona a linha completa
            current_line = word + " "  # Inicia nova linha com a palavra atual

    # Adiciona a última linha restante
    if current_line:
        lines.append(current_line.strip())

    # Junta as linhas com <br> para quebras no HTML
    return "<br>".join(lines)