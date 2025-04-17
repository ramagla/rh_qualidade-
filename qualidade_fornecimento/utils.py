import re

def extrair_bitola(descricao):
    """
    Extrai a bitola a partir do símbolo Ø na descrição.
    Exemplo: 'Ø0,70 ± 0,010' -> '0.70 mm'
    """
    match = re.search(r'Ø\s*([\d,\.]+)', descricao)
    if match:
        return match.group(1).replace(',', '.').strip() + " mm"
    return None

def extrair_norma(descricao):
    """
    Extrai normas reais como SAE 1018, SAE J403, NBR NM87-1010/1012, ignorando BTC/ATC etc.
    """
    if not descricao:
        return None

    descricao = descricao.upper()

    padroes = [
        r'(SAE\s?(?:J\d{3,5}|\d{4})(?:\s?/\s?\d{4})?)',
        r'(NBR\s?NM\s?87(?:[-–]?\d{4}(?:/\d{4})?)?)',
        r'(NBR\s?\d{4,5}(?:\s?\d{1,4})?)',
        r'(EN\s?\d{3,5}(?:[-–]\d{1,4})?)',
        r'(DIN\s?[A-Z]?\s?\d{3,5})',
        r'(ASTM\s?[A-Z]?\s?\d{2,5})'
    ]

    for padrao in padroes:
        match = re.search(padrao, descricao)
        if match:
            return match.group(1).strip()

    return None



def inferir_classe(descricao):
    """
    Infere a classe com base no conteúdo da descrição.
    Regras específicas para Inox, Carbono e outros.
    """
    if not descricao:
        return None

    descricao = descricao.lower()

    # Palavras-chave para identificar INOX
    inox_keywords = ['inox', '302', '304', '316', '430', 'nrb 13366']
    if any(kw in descricao for kw in inox_keywords):
        return 'Inox'

    # Palavras-chave para identificar CARBONO
    carbono_keywords = [
        'carbono', 'btc', 'din 17223', 'en 10270', 'nbr nm 87',
        'sae 1006', 'sae 1008', 'sae 1010', 'sae 1020', 'sae 1025'
    ]
    if any(kw in descricao for kw in carbono_keywords):
        return 'Carbono'

    # Palavras-chave para identificar LATÃO
    if 'latão' in descricao or 'c27000' in descricao or 'astm b134' in descricao:
        return 'Latão'

    return 'Outros'
