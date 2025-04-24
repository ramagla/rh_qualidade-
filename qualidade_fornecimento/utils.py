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


import io
import base64
import matplotlib.pyplot as plt
import numpy as np


def gerar_grafico_velocimetro(iqg):
    import io
    import base64
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.axis("off")

    # Cores e valores
    cores = ['#df5353', '#ffc107', '#28a745']
    limites = [0, 50, 75, 100]

    # Desenha as barras (faixas de cor)
    for i in range(len(cores)):
        theta = np.linspace(np.pi * (1 - (limites[i+1] / 100)), np.pi * (1 - (limites[i] / 100)), 100)
        ax.plot(np.cos(theta), np.sin(theta), lw=18, solid_capstyle='butt', color=cores[i])

    # Ponteiro
    angulo = np.pi * (1 - (iqg / 100))
    ax.plot([0, np.cos(angulo)], [0, np.sin(angulo)], lw=3, color='black')

    # Valor no centro (ajustado)
    ax.text(0, 0.3, f"{iqg:.0f}%", ha="center", va="center", fontsize=22, fontweight="bold")

    # Limites de visualização
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.1, 1.2)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", transparent=True)
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()
