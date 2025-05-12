from datetime import timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.db.models import DateField, ExpressionWrapper, F, Value
from django.template.loader import render_to_string
from django.utils.timezone import now

from alerts.models import Alerta, AlertaUsuario, AlertaConfigurado
from metrologia.models import Dispositivo, TabelaTecnica


@shared_task
def enviar_alertas_calibracao():
    today = now().date()
    range_end = today + timedelta(days=30)

    equipamentos = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            F("data_ultima_calibracao") + F("frequencia_calibracao") * timedelta(days=30),
            output_field=DateField(),
        )
    )
    dispositivos = Dispositivo.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            F("data_ultima_calibracao") + F("frequencia_calibracao") * Value(30),
            output_field=DateField(),
        )
    )

    conjuntos = {
        "vencida": {
            "equipamentos": equipamentos.filter(proxima_calibracao__lt=today),
            "dispositivos": dispositivos.filter(proxima_calibracao__lt=today),
            "alerta_in_app": "MANUTENCAO_VENCIDA",
            "mensagem": "está com a calibração vencida",
            "template": "alertas/calibracao_vencida.html",
        },
        "proxima": {
            "equipamentos": equipamentos.filter(proxima_calibracao__range=(today, range_end)),
            "dispositivos": dispositivos.filter(proxima_calibracao__range=(today, range_end)),
            "alerta_in_app": "MANUTENCAO_PROXIMA",
            "mensagem": "está com a calibração próxima do vencimento",
            "template": "alertas/calibracao_proxima.html",
        },
    }

    for chave, dados in conjuntos.items():
        # Envio por e-mail
        try:
            alerta_email = Alerta.objects.get(nome=chave)
        except Alerta.DoesNotExist:
            alerta_email = None

        # Alerta in-app
        try:
            config = AlertaConfigurado.objects.get(tipo=dados["alerta_in_app"], ativo=True)
            destinatarios_in_app = set(config.usuarios.all())
            for grupo in config.grupos.all():
                destinatarios_in_app.update(grupo.user_set.all())
        except AlertaConfigurado.DoesNotExist:
            destinatarios_in_app = set()

        # Dispositivos
        for dispositivo in dados["dispositivos"]:
            nome = dispositivo.codigo
            context = {
                "objeto": dispositivo,
                "proxima_calibracao": dispositivo.proxima_calibracao,
                "tipo": "dispositivos",
            }

            # E-mail
            if alerta_email:
                html_content = render_to_string(dados["template"], context)
                send_mail(
                    subject=f"Calibração {chave} para {nome}",
                    message=f"A calibração do dispositivo {nome} {dados['mensagem']}.",
                    from_email="no-reply@brasmol.com.br",
                    recipient_list=alerta_email.get_destinatarios_list(),
                    html_message=html_content,
                )

            # In-app
            for user in destinatarios_in_app:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo="🔧 Alerta de Calibração",
                    mensagem=f"O dispositivo {nome} {dados['mensagem']}.",
                )

        # Equipamentos
        for equipamento in dados["equipamentos"]:
            nome = equipamento.nome_equipamento
            context = {
                "objeto": equipamento,
                "proxima_calibracao": equipamento.proxima_calibracao,
                "tipo": "equipamentos",
            }

            # E-mail
            if alerta_email:
                html_content = render_to_string(dados["template"], context)
                send_mail(
                    subject=f"Calibração {chave} para {nome}",
                    message=f"A calibração do equipamento {nome} {dados['mensagem']}.",
                    from_email="no-reply@brasmol.com.br",
                    recipient_list=alerta_email.get_destinatarios_list(),
                    html_message=html_content,
                )

            # In-app
            for user in destinatarios_in_app:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo="🔧 Alerta de Calibração",
                    mensagem=f"O equipamento {nome} {dados['mensagem']}.",
                )
