import os
import django

# Configurar o Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rh_qualidade.settings")
django.setup()

from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

# Obtém a data atual
today = now().date()

# Buscar um equipamento para teste
equipamento = TabelaTecnica.objects.first()

if equipamento:
    print(f"Código: {equipamento.codigo}")
    print(f"Data Última Calibração: {equipamento.data_ultima_calibracao}")
    print(f"Frequência de Calibração (meses): {equipamento.frequencia_calibracao}")

    # Cálculo da próxima calibração
    if equipamento.data_ultima_calibracao and equipamento.frequencia_calibracao:
        proxima_calibracao = equipamento.data_ultima_calibracao + relativedelta(months=equipamento.frequencia_calibracao)
    else:
        proxima_calibracao = today  # Caso não tenha uma data definida

    print(f"Data Correta da Próxima Calibração: {proxima_calibracao}")
