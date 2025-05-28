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
def parse_decimal_seguro(value):
    """
    Converte string em Decimal, tratando 'nan', vazio ou nulo como None.
    """
    try:
        if value is None:
            return None
        val = str(value).strip().lower()
        if val in ("", "nan", "none"):
            return None
        return Decimal(val.replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return None


@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def lookup(d, key):
    try:
        return d[key]
    except (KeyError, TypeError, AttributeError):
        return None


@register.filter
def get_opcao_experiencia(obj, campo):
    valor = getattr(obj, campo, None)
    respostas = {
        'adaptacao_trabalho': {
            1: "Ruim (D) - Mantém um comportamento oposto ao solicitado para seu cargo e demonstra dificuldades de aceitação.",
            2: "Regular (C) - Precisa de muito esforço para se integrar ao trabalho e aos requisitos da Bras-Mol.",
            3: "Bom (B) - Faz o possível para integrar-se ao trabalho e às características da Bras-Mol.",
            4: "Ótimo (A) - Identifica-se plenamente com as atividades do cargo e normas da Bras-Mol.",
        },
        'interesse': {
            1: "Ruim (D) - Apresenta falta de entusiasmo e vontade de trabalhar.",
            2: "Regular (C) - Necessitará de estímulo constante para se interessar pelo trabalho.",
            3: "Bom (B) - Apresenta entusiasmo adequado para o tempo na Bras-Mol.",
            4: "Ótimo (A) - Demonstra vivo interesse pelo novo trabalho.",
        },
        'relacionamento_social': {
            1: "Ruim (D) - Sente-se perdido entre os colegas e parece não ter sido aceito.",
            2: "Regular (C) - Esforça-se para conseguir maior integração social com os colegas.",
            3: "Bom (B) - Entrosou-se bem e foi aceito sem resistência.",
            4: "Ótimo (A) - Demonstra grande habilidade em fazer amigos, sendo muito apreciado.",
        },
        'capacidade_aprendizagem': {
            1: "Ruim (D) - Parece não ter capacidade mínima para o trabalho.",
            2: "Regular (C) - Necessita de muito esforço e repetição para compreender as tarefas.",
            3: "Bom (B) - Aprende suas tarefas sem dificuldades.",
            4: "Ótimo (A) - Habilitado para o cargo, executa sem falhas.",
        }
    }
    return respostas.get(campo, {}).get(valor, "Não avaliado")


@register.filter
def split(value, delimiter=","):
    if isinstance(value, str):
        return value.split(delimiter)
    return []


@register.filter
def filter_status(queryset, status):
    return queryset.filter(status=status)

@register.filter
def dictfilter(queryset, attr):
    """
    Filtra objetos em uma queryset ou lista onde o atributo especificado não é None ou vazio.
    Ex: {{ funcionarios|dictfilter:"foto" }}
    """
    return [obj for obj in queryset if getattr(obj, attr, None)]

@register.filter
def formatar_duracao_flex(valor):
    """
    Converte decimal para hh:mm, preserva strings como '18h', e retorna '-' para valores inválidos.
    """
    try:
        # Se já está no formato string (ex: '18h', '1h', '00:45'), retorna como está
        if isinstance(valor, str):
            return valor.strip()

        total_minutos = int(float(valor) * 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60

        # Se for hora cheia
        if minutos == 0:
            return f"{horas}h"
        return f"{horas:02d}:{minutos:02d}"
    except (TypeError, ValueError):
        return "-"

PERFIL_ORDEM = {
    "oficial": 1,
    "suplente": 2,
    "treinado": 3,
    "em_treinamento": 4,
}

@register.filter
def ordenar_por_perfil(lista):
    return sorted(
        lista,
        key=lambda c: (PERFIL_ORDEM.get(c.get("perfil", ""), 999), c.get("nome", "").lower())
    )

@register.filter
def mascara_rg(value):
    if not value:
        return "—"
    value = str(value).zfill(9)  # garante 9 dígitos
    return f"{value[:2]}.{value[2:5]}.{value[5:8]}-{value[8]}"



from django import template
from datetime import datetime, timedelta

@register.simple_tag
def tempo_permanencia(entrada, saida):
    if entrada and saida:
        hoje = datetime.today()
        dt_entrada = datetime.combine(hoje, entrada)
        dt_saida = datetime.combine(hoje, saida)
        diferenca = dt_saida - dt_entrada
        horas, resto = divmod(diferenca.seconds, 3600)
        minutos = resto // 60
        return f"{horas}h {minutos}min"
    return "—"

import re

@register.filter
def mascarar_telefone(valor):
    if not valor:
        return ""
    valor = re.sub(r"\D", "", valor)  # remove tudo que não for número
    if len(valor) == 10:
        return f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
    elif len(valor) == 11:
        return f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
    return valor

@register.filter
def calcular_duracao(obj):
    """
    Recebe um objeto com data_inicio, hora_inicio, data_fim, hora_fim e retorna a duração como "hh:mm".
    """
    try:
        data_inicio = getattr(obj, "data_inicio", None)
        hora_inicio = getattr(obj, "hora_inicio", None)
        data_fim = getattr(obj, "data_fim", None)
        hora_fim = getattr(obj, "hora_fim", None)

        if None in [data_inicio, hora_inicio, data_fim, hora_fim]:
            return "-"

        dt_inicio = datetime.combine(data_inicio, hora_inicio)
        dt_fim = datetime.combine(data_fim, hora_fim)
        duracao = dt_fim - dt_inicio

        total_minutos = int(duracao.total_seconds() // 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60

        return f"{horas:02d}:{minutos:02d}"
    except Exception:
        return "-"

@register.filter
def subtrair(val1, val2):
    try:
        return float(val1 or 0) - float(val2 or 0)
    except Exception:
        return 0
    
from django.utils.safestring import mark_safe

@register.filter
def primeiro_ultimo_nome(nome_completo):
    """
    Retorna o primeiro e último nome de um nome completo em duas linhas.
    Ex: 'Maria José da Silva Oliveira' -> 'Maria<br>Oliveira'
    """
    if not nome_completo:
        return ""
    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return mark_safe(partes[0])
    return mark_safe(f"{partes[0]}<br>{partes[-1]}")