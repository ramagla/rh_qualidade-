# qualidade_fornecimento/services/avaliacao_rolo.py

from decimal import Decimal, InvalidOperation


def parse_decimal(value):
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, TypeError, AttributeError):
        return None


def avaliar_rolo(
    rolo,
    bitola_nominal,
    largura_nominal,
    tolerancia_esp,
    tolerancia_larg,
    res_min,
    res_max,
    dureza_limite,
):
    esp_ok = (
        rolo.bitola_espessura is not None
        and bitola_nominal is not None
        and (bitola_nominal - tolerancia_esp)
        <= rolo.bitola_espessura
        <= (bitola_nominal + tolerancia_esp)
    )

    lar_ok = (
        rolo.bitola_largura is not None
        and largura_nominal is not None
        and (largura_nominal - tolerancia_larg)
        <= rolo.bitola_largura
        <= (largura_nominal + tolerancia_larg)
    )

    tracao_ok = (
        rolo.tracao is not None
        and res_min is not None
        and res_max is not None
        and res_min <= rolo.tracao <= res_max
    )

    dureza_ok = rolo.dureza is None or (
        dureza_limite is not None and rolo.dureza <= dureza_limite
    )

    extras_ok = all(
        [
            rolo.enrolamento == "OK",
            rolo.dobramento == "OK",
            rolo.torcao_residual == "OK",
            rolo.aspecto_visual == "OK",
        ]
    )

    aprovado = all([esp_ok, lar_ok, tracao_ok, dureza_ok, extras_ok])
    rolo.laudo = "Aprovado" if aprovado else "Reprovado"
    return rolo
