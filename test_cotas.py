from django.http import QueryDict

from metrologia.models import Cota, Dispositivo

# Simular dados do formulário
data = QueryDict("", mutable=True)
data.update(
    {
        "codigo_dispositivo": "7",
        "instrumento_utilizado": "66",
        "nome_responsavel": "30",
        "data_afericao": "2017-05-30",
        "afericoes[1]": "13.76",
        "afericoes[2]": "14.16",
        "observacoes": "Teste de calibração",
    }
)

# Obter o dispositivo pelo ID
dispositivo_id = data.get("codigo_dispositivo")
dispositivo = Dispositivo.objects.get(id=dispositivo_id)
print(f"Dispositivo: {dispositivo}")

# Listar cotas associadas ao dispositivo
cotas = dispositivo.cotas.all()
print("Cotas do dispositivo:")
for cota in cotas:
    print(f" - Cota {cota.numero}: {cota.valor_minimo} a {cota.valor_maximo}")

# Processar as aferições
for key, value in data.items():
    if key.startswith("afericoes["):
        cota_numero = key.split("[")[1].split("]")[0]
        print(f"Processando cota número: {cota_numero}")

        if not cota_numero.isdigit():
            print(f"Erro: Número inválido: {cota_numero}")
            continue

        cota = Cota.objects.filter(numero=cota_numero, dispositivo=dispositivo).first()
        if cota:
            print(f" - Cota encontrada: {cota.numero}")
            valor = float(value.replace(",", "."))
            print(f" - Valor da aferição: {valor}")
            print(f" - Limites da cota: {cota.valor_minimo} a {cota.valor_maximo}")

            status = (
                "Aprovado"
                if cota.valor_minimo <= valor <= cota.valor_maximo
                else "Reprovado"
            )
            print(f" - Status: {status}")
        else:
            print(
                f"Erro: Cota {cota_numero} não encontrada para o dispositivo {dispositivo.codigo}"
            )
