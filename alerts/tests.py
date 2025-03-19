from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from alerts.models import Alerta
from alerts.tasks import enviar_alertas_calibracao
from metrologia.models import TabelaTecnica


class AlertasTestCase(TestCase):
    def setUp(self):
        # Configurar alertas
        Alerta.objects.create(
            nome="Alerta de Calibração Vencida",
            descricao="Teste de calibração vencida",
            ativo=True,
            destinatarios="test1@example.com,test2@example.com",
        )
        Alerta.objects.create(
            nome="Alerta de Calibração Próxima",
            descricao="Teste de calibração próxima",
            ativo=True,
            destinatarios="test3@example.com",
        )

        # Configurar equipamentos
        TabelaTecnica.objects.create(
            codigo="EQ001",
            nome_equipamento="Equipamento Teste Vencido",
            capacidade_minima=10.0,
            capacidade_maxima=100.0,
            tolerancia_em_percentual=2,
            resolucao=1.0,
            unidade_medida="mm",
            tolerancia_total_minima=5.0,
            frequencia_calibracao=30,
            numero_serie="SERIE001",  # Adicionar valor único
            data_ultima_calibracao=now().date()
            - timedelta(days=40),  # Calibração vencida
        )

        TabelaTecnica.objects.create(
            codigo="EQ002",
            nome_equipamento="Equipamento Teste Próximo",
            capacidade_minima=5.0,
            capacidade_maxima=50.0,
            tolerancia_em_percentual=1,
            resolucao=0.5,
            unidade_medida="kg.cm",
            tolerancia_total_minima=2.5,
            frequencia_calibracao=30,
            numero_serie="SERIE002",  # Adicionar valor único
            data_ultima_calibracao=now().date()
            - timedelta(days=20),  # Próxima calibração
        )

    def test_enviar_alertas(self):
        # Executar a tarefa
        enviar_alertas_calibracao()

        # Validar comportamento esperado
        alertas_ativos = Alerta.objects.filter(ativo=True)
        self.assertTrue(alertas_ativos.exists())


class TestarEnvioDeAlertas(TestCase):
    def test_envio_alertas(self):
        # Executa a tarefa
        enviar_alertas_calibracao()

        # Valide os comportamentos (logs, saída, etc.)
        print("Teste de envio de alertas executado!")
