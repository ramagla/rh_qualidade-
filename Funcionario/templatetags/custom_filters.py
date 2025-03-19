import os
from datetime import timedelta
from urllib.parse import parse_qs, urlencode

from dateutil.relativedelta import relativedelta
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
    return field.as_widget(attrs={"class": css_class})


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
            current_line += word + " "
        else:
            lines.append(current_line.strip())  # Adiciona a linha completa
            current_line = word + " "  # Inicia nova linha com a palavra atual

    # Adiciona a última linha restante
    if current_line:
        lines.append(current_line.strip())

    # Junta as linhas com <br> para quebras no HTML
    return "<br>".join(lines)


@register.filter
def sum_values(queryset, field_name):
    return sum(getattr(obj, field_name, 0) for obj in queryset)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def dict(value, key):
    return value.get(key, "")


@register.filter
def primeiro_nome(nome_completo):
    """Retorna apenas o primeiro nome de um nome completo."""
    return nome_completo.split()[0] if nome_completo else ""


@register.filter
def default_if_none(value, default="Não informado"):
    """Retorna um valor padrão se o valor for None ou vazio"""
    return value if value else default


@register.filter
def split_by_comma(value):
    """Divide uma string por vírgulas e retorna uma lista"""
    if value:
        return value.split(",")
    return []


@register.filter
def remove_query_param(querystring, param):
    """
    Remove o parâmetro especificado do querystring.
    """
    query_dict = parse_qs(querystring)
    query_dict.pop(param, None)  # Remove o parâmetro, se existir
    return urlencode(query_dict, doseq=True)


@register.filter
def basename(value):
    """
    Retorna apenas o nome do arquivo sem o caminho completo.
    """
    return os.path.basename(value)


@register.filter
def add_days(value, days):
    """
    Adiciona 'days' dias à data fornecida.
    """
    if value:
        return value + timedelta(days=days)
    return value


@register.filter
def add_months(date, months):
    if date:
        return date + relativedelta(months=months)
    return None


@register.filter
def add_attribute(field, args):
    """
    Adiciona atributos ao widget de um campo do formulário.
    Uso no template: {{ field|add_attribute:"key:value" }}
    """
    key, value = args.split(":")
    field.field.widget.attrs[key] = value
    return field


@register.filter
def has_permission(user, perm):
    """Verifica se o usuário possui uma permissão específica."""
    return user.has_perm(perm)
