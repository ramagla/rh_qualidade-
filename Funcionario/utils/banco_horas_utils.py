from datetime import datetime, timedelta


def parse_horas_trabalhadas(horas_str):
    """Converte string de horas no formato ±HH:MM em timedelta."""
    negativo = horas_str.startswith("-")
    horas_str = horas_str.lstrip("+-")
    partes = horas_str.split(":")
    if len(partes) != 2:
        return None
    try:
        horas = int(partes[0])
        minutos = int(partes[1])
        td = timedelta(hours=horas, minutes=minutos)
        return -td if negativo else td
    except ValueError:
        return None


def calcular_saldo(hora_entrada, hora_saida):
    """Calcula o saldo de horas com base na entrada e saída considerando jornada de 8h."""
    if hora_entrada and hora_saida:
        entrada = datetime.combine(datetime.today(), hora_entrada)
        saida = datetime.combine(datetime.today(), hora_saida)
        duracao = (saida - entrada).total_seconds() / 3600
        saldo = duracao - 8
        return round(saldo, 2)
    return None
