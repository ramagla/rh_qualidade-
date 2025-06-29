import re
from Funcionario.models.matriz_polivalencia import Atividade

# Lista de abreviações padronizadas (reutilizável em qualquer função)
ABREVIACOES_PADRAO = {
    "CEO", "USA", "UN", "EU", "UNESCO", "FMEA", "APQP", "POQ", "PQ", "SAC", "CQI",
    "GLP", "LGPD", "PPP", "DP", "RH", "IMDS", "VDA", "AIAG", "CEP", "MSA", "PPAP",
    "NR", "NBR", "ISO", "IATF", "CLP", "PPRS", "TS", "PPCP", "IO", "SGI", "CNC",
    "EPIs", "II", "III", "PIST", "PIPC", "SGS", "SGQ", "CIPA", "CQI-11", "CQI-12", "CQI-9","MP", "ERP", "NF",
    "NFs", "IQF", "IQG", "CAD", "TI", "PCP", "SAC's", "CQ"
}


def formatar_nome_atividade_com_siglas(texto):
    """
    Formata o texto colocando apenas a primeira letra em maiúscula
    e as abreviações reconhecidas (como CIPA, FMEA) em caixa alta.
    Exemplo: "inspeção com cipa e fmea obrigatórias" -> "Inspeção com CIPA e FMEA obrigatórias"
    """
    if not texto:
        return texto

    palavras = texto.lower().split()
    resultado = []

    for palavra in palavras:
        # Remove pontuação temporariamente para verificar abreviações
        palavra_limpa = re.sub(r"[^\w\d]", "", palavra).upper()
        if palavra_limpa in ABREVIACOES_PADRAO:
            resultado.append(palavra_limpa)
        else:
            resultado.append(palavra)

    frase = " ".join(resultado)
    return frase[0].upper() + frase[1:] if frase else ""


def title_case(text):
    """
    Aplica capitalização tipo 'title case', mas mantendo exceções (preposições) em minúsculo
    e siglas reconhecidas em maiúsculo.
    """
    exceptions = [
        "a", "o", "as", "os", "uma", "um", "umas", "uns",
        "e", "ou", "nem", "mas", "por", "para", "com", "sem",
        "de", "do", "da", "dos", "das", "entre", "sob", "sobre",
        "até", "como", "quando", "quanto", "que", "porque", "pois",
        "em", "no"
    ]

    abbreviation_pattern = re.compile(r"([A-Z]+)(\d+)$", re.IGNORECASE)
    words = text.split()
    for i in range(len(words)):
        word = words[i]
        if word.lower() in exceptions:
            words[i] = word.lower()
        else:
            match = abbreviation_pattern.match(word)
            if match:
                prefix, number = match.groups()
                if prefix.upper() in ABREVIACOES_PADRAO:
                    words[i] = f"{prefix.upper()}{number}"
                else:
                    words[i] = word.capitalize()
            elif word.upper() in ABREVIACOES_PADRAO:
                words[i] = word.upper()
            else:
                words[i] = word.capitalize()
    return " ".join(words)


def obter_atividades_com_fixas(departamento):
    """
    Retorna uma lista de atividades do departamento com as duas atividades fixas
    sempre ao final, sem duplicar.
    """
    atividades = list(Atividade.objects.filter(departamentos=departamento))

    nomes_fixos = [
        "manter o setor limpo e organizado",
        "manusear e descartar materiais, resíduos e sucatas",
    ]

    atividades_fixas = [a for a in atividades if a.nome.lower() in nomes_fixos]
    atividades_outros = [a for a in atividades if a.nome.lower() not in nomes_fixos]

    return atividades_outros + atividades_fixas


import fitz  # PyMuPDF
from decimal import Decimal
import re

def extrair_valores_recibo(conteudo_pdf: bytes):
    try:
        doc = fitz.open(stream=conteudo_pdf, filetype="pdf")
        texto = "\n".join(page.get_text() for page in doc)
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]

        def valor_decimal(linha):
            try:
                return Decimal(linha.replace('.', '').replace(',', '.'))
            except Exception:
                return None

        # Busca a linha que contém a frase final
        idx_base = -1
        for i, linha in enumerate(linhas):
            if "recebido a importância líquida" in linha.lower():
                idx_base = i
                break

        valores = []
        if idx_base != -1:
            for l in linhas[idx_base + 1:]:
                if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", l):
                    v = valor_decimal(l)
                    if v is not None:
                        valores.append(v)
                    if len(valores) == 3:
                        break

        if len(valores) == 3:
            valor_total, valor_descontos, valor_liquido = valores
        else:
            valor_total = valor_descontos = valor_liquido = None

        print(f"[EXTRAÇÃO FINAL] Total={valor_total}, Descontos={valor_descontos}, Líquido={valor_liquido}")

        return {
            "valor_total": valor_total,
            "valor_descontos": valor_descontos,
            "valor_liquido": valor_liquido,
        }

    except Exception as e:
        print(f"[ERRO] Falha na extração dos valores: {e}")
        return {}
