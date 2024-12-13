from celery import shared_task
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.db.models import ExpressionWrapper, F, DateField
from alerts.models import Alerta
from metrologia.models import TabelaTecnica

@shared_task
def enviar_alertas_calibracao():
    today = now().date()
    range_end = today + timedelta(days=30)

    # Adicionar anotação para calcular a próxima calibração usando ExpressionWrapper
    equipamentos = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            F('data_ultima_calibracao') + F('frequencia_calibracao') * timedelta(days=30),
            output_field=DateField()
        )
    )

    # Equipamentos vencidos
    vencidos = equipamentos.filter(proxima_calibracao__lt=today)

    # Equipamentos próximos do vencimento
    proximos = equipamentos.filter(
        proxima_calibracao__gte=today,
        proxima_calibracao__lte=range_end
    )

    # Buscar os alertas ativos
    try:
        alerta_vencidos = Alerta.objects.get(nome='vencida')
    except Alerta.DoesNotExist:
        print("Nenhum alerta configurado para calibração vencida.")
        alerta_vencidos = None

    try:
        alerta_proximos = Alerta.objects.get(nome='proxima')
    except Alerta.DoesNotExist:
        print("Nenhum alerta configurado para calibração próxima.")
        alerta_proximos = None

    # Enviar e-mails para equipamentos vencidos
    if alerta_vencidos:
        for equipamento in vencidos:
            html_content = render_to_string(
                'alertas/calibracao_vencida.html',
                {'equipamento': equipamento, 'proxima_calibracao': equipamento.proxima_calibracao}
            )
            send_mail(
                subject=f'Calibração vencida para {equipamento.nome_equipamento}',
                message=f'O equipamento {equipamento.nome_equipamento} está com a calibração vencida.',
                from_email='no-reply@brasmol.com.br',
                recipient_list=alerta_vencidos.get_destinatarios_list(),
                html_message=html_content
            )
            print(f"E-mail enviado para o equipamento vencido: {equipamento.nome_equipamento}")

    # Enviar e-mails para equipamentos próximos do vencimento
    if alerta_proximos:
        for equipamento in proximos:
            html_content = render_to_string(
                'alertas/calibracao_proxima.html',
                {'equipamento': equipamento, 'proxima_calibracao': equipamento.proxima_calibracao}
            )
            send_mail(
                subject=f'Calibração próxima para {equipamento.nome_equipamento}',
                message=f'O equipamento {equipamento.nome_equipamento} está próximo da data de calibração.',
                from_email='no-reply@brasmol.com.br',
                recipient_list=alerta_proximos.get_destinatarios_list(),
                html_message=html_content
            )
            print(f"E-mail enviado para o equipamento próximo: {equipamento.nome_equipamento}")
