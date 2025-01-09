from celery import shared_task
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.db.models import ExpressionWrapper, F, DateField, Value
from alerts.models import Alerta
from metrologia.models import TabelaTecnica, Dispositivo

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

    dispositivos = Dispositivo.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            F('data_ultima_calibracao') + F('frequencia_calibracao') * Value(30),
            output_field=DateField()
        )
    )

    objetos = {
        'vencidos': {
            'equipamentos': equipamentos.filter(proxima_calibracao__lt=today),
            'dispositivos': dispositivos.filter(proxima_calibracao__lt=today),
        },
        'proximos': {
            'equipamentos': equipamentos.filter(
                proxima_calibracao__gte=today,
                proxima_calibracao__lte=range_end
            ),
            'dispositivos': dispositivos.filter(
                proxima_calibracao__gte=today,
                proxima_calibracao__lte=range_end
            ),
        },
    }

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

    # Enviar e-mails para objetos vencidos
    if alerta_vencidos:
        for tipo, colecao in objetos['vencidos'].items():
            for obj in colecao:
                html_content = render_to_string(
                    'alertas/calibracao_vencida.html',
                    {'objeto': obj, 'proxima_calibracao': obj.proxima_calibracao, 'tipo': tipo}
                )
                send_mail(
                    subject=f'Calibração vencida para {obj.nome_equipamento if tipo == "equipamentos" else obj.codigo}',
                    message=f'A calibração do {tipo[:-1]} está vencida.',
                    from_email='no-reply@brasmol.com.br',
                    recipient_list=alerta_vencidos.get_destinatarios_list(),
                    html_message=html_content
                )
                print(f"E-mail enviado para o {tipo[:-1]} vencido: {obj.nome_equipamento if tipo == 'equipamentos' else obj.codigo}")

    # Enviar e-mails para objetos próximos do vencimento
    if alerta_proximos:
        for tipo, colecao in objetos['proximos'].items():
            for obj in colecao:
                html_content = render_to_string(
                    'alertas/calibracao_proxima.html',
                    {'objeto': obj, 'proxima_calibracao': obj.proxima_calibracao, 'tipo': tipo}
                )
                send_mail(
                    subject=f'Calibração próxima para {obj.nome_equipamento if tipo == "equipamentos" else obj.codigo}',
                    message=f'A calibração do {tipo[:-1]} está próxima.',
                    from_email='no-reply@brasmol.com.br',
                    recipient_list=alerta_proximos.get_destinatarios_list(),
                    html_message=html_content
                )
                print(f"E-mail enviado para o {tipo[:-1]} próximo: {obj.nome_equipamento if tipo == 'equipamentos' else obj.codigo}")