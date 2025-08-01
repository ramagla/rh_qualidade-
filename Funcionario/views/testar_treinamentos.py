from Funcionario.models import Treinamento, Funcionario
from Funcionario.utils.relatorios_utils import dividir_horas_por_trimestre
from datetime import datetime

# Defina o ano e o intervalo de meses do 3º trimestre
ano = 2025
mes_inicio, mes_fim = 7, 9  # Julho a Setembro

# Filtrar treinamentos concluídos no 3º trimestre
treinamentos = Treinamento.objects.filter(
    data_inicio__year=ano,
    data_inicio__month__gte=mes_inicio,
    data_inicio__month__lte=mes_fim,
    status="concluido"
)

print(f"Treinamentos encontrados no 3º trimestre de {ano}: {treinamentos.count()}")

for t in treinamentos:
    # Pega a carga horária numérica
    carga = float(t.carga_horaria.replace("h", "").strip() or 0)

    # Busca participantes únicos pelo nome e data do curso
    participantes = Funcionario.objects.filter(
        treinamentos__nome_curso=t.nome_curso,
        treinamentos__data_inicio=t.data_inicio
    ).distinct().count()

    total = carga * participantes
    distribuicao = dividir_horas_por_trimestre(t.data_inicio, t.data_fim, total)

    print(f"\n📝 Curso: {t.nome_curso}")
    print(f"📅 Período: {t.data_inicio.strftime('%d/%m/%Y')} a {t.data_fim.strftime('%d/%m/%Y')}")
    print(f"👥 Participantes: {participantes}")
    print(f"⏱ Carga Total Estimada: {total:.2f} horas")
    print(f"📊 Distribuição por Trimestre: {distribuicao}")
