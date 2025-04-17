# utils.py
import re


def title_case(text):
    # Lista de palavras para manter em minúsculas (artigos, preposições, conjunções)
    exceptions = [
        "a",
        "o",
        "as",
        "os",
        "uma",
        "um",
        "umas",
        "uns",  # Artigos em português
        "e",
        "ou",
        "nem",
        "mas",
        "por",
        "para",
        "com",
        "sem",
        "de",
        "do",
        "da",
        "dos",
        "das",
        "entre",
        "sob",
        "sobre",
        "até",
        "como",
        "quando",
        "quanto",
        "que",
        "porque",
        "pois",
        "em",
        "no",
    ]

    # Lista de abreviações para manter em maiúsculas, incluindo prefixos que podem ter números
    abbreviations = [
        "CEO",
        "USA",
        "UN",
        "EU",
        "UNESCO",
        "FMEA",
        "APQP",
        "POQ",
        "PQ",
        "SAC",
        "CQI",
        "GLP",
        "LGPD",
        "PPP",
        "DP",
        "RH",
        "IMDS",
        "VDA",
        "AIAG",
        "CEP",
        "MSA",
        "PPAP",
        "NR",
        "NBR",
        "ISO",
        "IATF",
        "CLP",
        "PPRS",
        "TS",
        "PPCP",
        "IO",
        "SGI",
        "CNC",
        "EPIs",
        "II",
        "III",
        "PIST",
        "PIPC",
        "SGS",
        "SGQ",
    ]

    # Expressão regular para detectar abreviações seguidas de números (ex: POQ001, PQ002)
    abbreviation_pattern = re.compile(r"([A-Z]+)(\d+)$", re.IGNORECASE)

    # Divide o texto em palavras
    words = text.split()
    for i in range(len(words)):
        word = words[i]

        # Verifica se a palavra é uma exceção (artigo ou preposição)
        if word.lower() in exceptions:
            words[i] = word.lower()  # Mantém em minúsculas
        else:
            match = abbreviation_pattern.match(word)
            if match:
                prefix, number = match.groups()
                if prefix.upper() in abbreviations:
                    # Mantém o prefixo em maiúsculas e mantém os números
                    words[i] = f"{prefix.upper()}{number}"
                else:
                    words[i] = word.capitalize()
            elif word.upper() in abbreviations:
                words[i] = word.upper()  # Mantém em maiúsculas
            else:
                words[i] = word.capitalize()  # Capitaliza normalmente

    # Junta as palavras novamente e retorna
    return " ".join(words)


# Teste
text = "o projeto poq001 foi enviado para a pq002 e aprovado pelo ceo"
print(title_case(text))


