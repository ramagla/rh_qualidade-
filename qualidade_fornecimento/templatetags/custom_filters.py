import os
from datetime import timedelta
from urllib.parse import parse_qs, urlencode
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta
from django import template

register = template.Library()

# ---------------------------------------
# FILTROS DE DICIONÁRIO / ATRIBUTOS
# ---------------------------------------

@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""

@register.filter
def duracao_em_horas(valor):
    try:
        horas = int(valor)
        minutos = round((valor - horas) * 60)
        return f"{horas:02d}:{minutos:02d}"
    except:
        return valor
    
@register.filter
def formatar_duracao(valor):
    try:
        total_minutos = int(float(valor) * 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60
        return f"{horas:02d}:{minutos:02d}"
    except (TypeError, ValueError):
        return "-"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def dict(value, key):
    return value.get(key, "")

@register.filter
def get_nested_item(dictionary, keys):
    try:
        key1, key2 = keys.split(",")
        return dictionary.get(key1, {}).get(key2)
    except (ValueError, AttributeError):
        return None

@register.filter
def attr(obj, attr_name):
    try:
        return getattr(obj, attr_name)
    except Exception:
        return ""

# ---------------------------------------
# FILTROS DE CAMPOS DE FORMULÁRIO
# ---------------------------------------

@register.filter
def add_attrs(field, attrs: str):
    final_attrs = {}
    for attr in attrs.split(","):
        key, val = attr.split("=")
        final_attrs[key.strip()] = val.strip()
    return field.as_widget(attrs=final_attrs)

@register.filter
def add_attribute(field, args):
    key, value = args.split(":")
    field.field.widget.attrs[key] = value
    return field

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

# ---------------------------------------
# FILTROS DE TEXTO / NOMES
# ---------------------------------------

@register.filter
def auto_breaks(value, max_length=20):
    words = value.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return "<br>".join(lines)

@register.filter
def split_by_comma(value):
    return value.split(",") if value else []

@register.filter
def primeiro_nome(nome_completo):
    return nome_completo.split()[0] if nome_completo else ""

@register.filter
def default_if_none(value, default="Não informado"):
    return value if value else default

# ---------------------------------------
# FILTROS DE PERMISSÃO / HTML
# ---------------------------------------

@register.filter
def has_permission(user, perm):
    return user.has_perm(perm)

@register.filter
def basename(value):
    return os.path.basename(value)

@register.filter
def remove_query_param(querystring, param):
    query_dict = parse_qs(querystring)
    query_dict.pop(param, None)
    return urlencode(query_dict, doseq=True)

# ---------------------------------------
# FILTROS DE DATA / TEMPO
# ---------------------------------------

@register.filter
def add_days(value, days):
    try:
        return value + timedelta(days=int(days))
    except Exception:
        return value

@register.filter
def add_months(date, months):
    if date:
        return date + relativedelta(months=months)
    return None

# ---------------------------------------
# FILTROS NUMÉRICOS / CÁLCULO
# ---------------------------------------

@register.filter
def sum_values(queryset, field_name):
    return sum(getattr(obj, field_name, 0) for obj in queryset)

@register.filter
def calc_peso_total(rolos):
    return sum([rolo.peso or 0 for rolo in rolos])

@register.filter
def parse_decimal(value):
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def lookup(d, key):
    try:
        return d[key]
    except (KeyError, TypeError, AttributeError):
        return None
