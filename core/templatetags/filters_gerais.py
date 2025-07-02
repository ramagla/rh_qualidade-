from django import template
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from dateutil.relativedelta import relativedelta
import os
import re

from rh_qualidade.utils import title_case, formatar_nome_atividade_com_siglas

register = template.Library()

# -------------------------------
# FILTROS DE DICIONÁRIO / ATRIBUTOS
# -------------------------------

@register.filter
def dict_get(d, key):
    """Retorna o valor de uma chave em dicionário."""
    return d.get(key, "")

@register.filter
def get_nested_item(dictionary, keys):
    """Acessa valor aninhado com duas chaves separadas por vírgula."""
    try:
        key1, key2 = keys.split(",")
        return dictionary.get(key1, {}).get(key2)
    except Exception:
        return None

@register.filter
def attr(obj, attr_name):
    """Retorna um atributo de um objeto."""
    try:
        return getattr(obj, attr_name)
    except Exception:
        return ""

# -------------------------------
# FILTROS DE FORMULÁRIO
# -------------------------------

@register.filter
def add_class(field, css_class):
    """Adiciona classe CSS a um campo de formulário."""
    from django.forms.boundfield import BoundField
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    return field

@register.filter
def add_attribute(field, args):
    """Adiciona um atributo a um campo de formulário (ex: placeholder:Texto)."""
    key, value = args.split(":")
    field.field.widget.attrs[key] = value
    return field

@register.filter
def add_attrs(field, attrs: str):
    """Adiciona múltiplos atributos ao widget (ex: 'placeholder=Digite,class=form-control')."""
    final_attrs = {}
    for attr in attrs.split(","):
        key, val = attr.split("=")
        final_attrs[key.strip()] = val.strip()
    return field.as_widget(attrs=final_attrs)

# -------------------------------
# TEXTO / NOMES / FORMATOS
# -------------------------------

@register.filter
def primeiro_nome(nome_completo):
    return nome_completo.split()[0] if nome_completo else ""

@register.filter
def primeiro_ultimo_nome(nome_completo):
    if not nome_completo:
        return ""
    partes = nome_completo.strip().split()
    return mark_safe(f"{partes[0]}<br>{partes[-1]}" if len(partes) > 1 else partes[0])

@register.filter
def primeiro_ultimo_nome_inline(nome_completo):
    if not nome_completo:
        return ""
    partes = nome_completo.strip().split()
    return f"{partes[0]} {partes[-1]}" if len(partes) > 1 else partes[0]

@register.filter
def split_by_comma(value):
    return value.split(",") if value else []

@register.filter
def formatar_titulo(texto):
    return title_case(texto)

@register.filter(name="formatar_siglas")
def formatar_siglas(texto):
    return formatar_nome_atividade_com_siglas(texto)

@register.filter
def auto_breaks(value, max_length=20):
    """Insere <br> em strings longas para layout responsivo."""
    words = value.split()
    lines, current_line = [], ""
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
def default_if_none(value, default="Não informado"):
    return value if value else default

# -------------------------------
# DATA / HORA / DURAÇÃO
# -------------------------------

@register.filter
def formatar_duracao(valor):
    try:
        total_minutos = int(float(valor) * 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60
        return f"{horas:02d}:{minutos:02d}"
    except Exception:
        return "-"

@register.filter
def formatar_duracao_flex(valor):
    try:
        if isinstance(valor, str):
            return valor.strip()
        total_minutos = int(float(valor) * 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60
        return f"{horas}h" if minutos == 0 else f"{horas:02d}:{minutos:02d}"
    except Exception:
        return "-"

@register.filter
def calcular_duracao(obj):
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
        return f"{total_minutos//60:02d}:{total_minutos%60:02d}"
    except Exception:
        return "-"

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

@register.filter
def extrair_mes_ano(valor):
    try:
        partes = valor.split("-")
        return f"{partes[1]}/{partes[0]}"
    except:
        return valor

@register.filter
def to(value, arg):
    try:
        return range(int(value), int(arg)+1)
    except:
        return []

# -------------------------------
# NUMÉRICOS / CÁLCULO
# -------------------------------

@register.filter
def parse_decimal_seguro(value):
    try:
        if value is None:
            return None
        val = str(value).strip().lower()
        if val in ("", "nan", "none"):
            return None
        return Decimal(val.replace(",", "."))
    except Exception:
        return None

@register.filter
def subtrair(val1, val2):
    try:
        return float(val1 or 0) - float(val2 or 0)
    except Exception:
        return 0

@register.filter
def separador_milhar(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except:
        return valor

# -------------------------------
# FORMATADORES VISUAIS
# -------------------------------

@register.filter
def mascarar_telefone(valor):
    if not valor:
        return ""
    valor = re.sub(r"\D", "", valor)
    if len(valor) == 10:
        return f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
    elif len(valor) == 11:
        return f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
    return valor

@register.filter
def formatar_op(numero_op):
    if not numero_op:
        return ""
    op = str(numero_op).zfill(6)
    return f"{op[:3]}.{op[3:]}"


@register.filter
def lookup(form, field_name):
    """Retorna o campo do form baseado no nome dinâmico."""
    return form[field_name]



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

@register.filter
def menor_que(data1, data2_str):
    """
    Compara se data1 < data2.
    data2_str deve estar no formato 'YYYY-MM-DD'
    """
    if not data1 or not data2_str:
        return False

    try:
        data2 = datetime.strptime(data2_str, "%Y-%m-%d").date()
        return data1 < data2
    except Exception:
        return False
    

@register.filter(name='peso_total_blocos')
def peso_total_blocos(itens):
    """
    Soma o peso_total de todos os itens passados (QuerySet ou lista).
    """
    try:
        return sum(getattr(i, "peso_total", 0) or 0 for i in itens)
    except Exception:
        return 0

