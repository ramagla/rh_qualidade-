# Standard library
from datetime import timedelta

# Terceiros
from celery import shared_task

# Django
from django.core.mail import send_mail
from django.db.models import DateField, ExpressionWrapper, F, Value
from django.template.loader import render_to_string
from django.utils.timezone import now

# Apps locais
from alerts.models import Alerta, AlertaUsuario, AlertaConfigurado
from metrologia.models import Dispositivo, TabelaTecnica
from qualidade_fornecimento.models import FornecedorQualificado


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
            nome = f"{dispositivo.codigo} – {dispositivo.descricao}"
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
                    titulo = "📟 Calibração de Dispositivo Vencida" if chave == "vencida" else "🕒 Calibração de Dispositivo Próxima",
                    mensagem = f"O dispositivo {nome} {dados['mensagem']}."
                )

        # Equipamentos
        for equipamento in dados["equipamentos"]:
            nome = f"{equipamento.codigo} – {equipamento.nome_equipamento}"
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
                    titulo = "🔩 Calibração de Equipamento Vencida" if chave == "vencida" else "🕒 Calibração de Equipamento Próxima",
                    mensagem = f"O equipamento {nome} {dados['mensagem']}."

                )
@shared_task
def enviar_alertas_fornecedores_proximos():
    today = now().date()
    range_end = today + timedelta(days=30)
    fornecedores = FornecedorQualificado.objects.all()

    def disparar_alerta(tipo_alerta, campo_data, titulo, campo_nome):
        try:
            config = AlertaConfigurado.objects.get(tipo=tipo_alerta, ativo=True)
            destinatarios = set(config.usuarios.all())
            for grupo in config.grupos.all():
                destinatarios.update(grupo.user_set.all())
        except AlertaConfigurado.DoesNotExist:
            return

        proximos = fornecedores.filter(**{
            f"{campo_data}__range": (today, range_end)
        })

        for fornecedor in proximos:
            nome = fornecedor.nome
            data_evento = getattr(fornecedor, campo_data)
            mensagem = f"O fornecedor {nome} tem {campo_nome} prevista para {data_evento.strftime('%d/%m/%Y')}."

            for user in destinatarios:
                # Alerta in-app
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo=titulo,
                    mensagem=mensagem,
                    tipo=tipo_alerta,
                    referencia_id=fornecedor.id,
                    url_destino=f"/fornecedores/{fornecedor.id}/visualizar/",
                )

                # E-mail (se e-mail do usuário estiver preenchido)
                if user.email:
                    send_mail(
                        subject=titulo,
                        message=mensagem,
                        from_email="no-reply@brasmol.com.br",
                        recipient_list=[user.email],
                        fail_silently=True,
                    )

    disparar_alerta(
        "AVALIACAO_RISCO_PROXIMA",
        "proxima_avaliacao_risco",
        "⚠️ Avaliação de Risco Próxima",
        "a próxima avaliação de risco"
    )

    disparar_alerta(
        "AUDITORIA_PROXIMA",
        "proxima_auditoria",
        "📝 Auditoria Próxima",
        "a próxima auditoria"
    )

    disparar_alerta(
        "CERTIFICACAO_PROXIMA",
        "vencimento_certificacao",
        "🏅 Certificação Próxima do Vencimento",
        "a certificação vencendo"
    )
