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


def _eom(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


@shared_task
def enviar_alertas_calibracao():
    """
    Envia alertas de calibração:
    - 'vencida': proxima_calibracao < hoje
    - 'proxima': hoje <= proxima_calibracao <= hoje+30
    Regras:
      • Próxima calibração calculada com fim-do-mês.
      • Apenas EQUIPAMENTOS ativos (TabelaTecnica.status='ativo') geram e-mail.
      • Dispositivos seguem a mesma lógica de datas (EOM).
    """
    today = now().date()
    range_end = today + timedelta(days=30)

    # -----------------------
    # EQUIPAMENTOS (somente ativos)
    # -----------------------
    equipamentos_qs = TabelaTecnica.objects.filter(status="ativo")
    equipamentos_vencidos = []
    equipamentos_proximos = []

    for eq in equipamentos_qs:
        if not (eq.data_ultima_calibracao and eq.frequencia_calibracao):
            continue
        prox = _eom(eq.data_ultima_calibracao + relativedelta(months=eq.frequencia_calibracao))
        setattr(eq, "proxima_calibracao", prox)
        if prox < today:
            equipamentos_vencidos.append(eq)
        elif today <= prox <= range_end:
            equipamentos_proximos.append(eq)

    # -----------------------
    # DISPOSITIVOS (mantido sem filtro de 'ativo' pois o modelo não expõe status)
    # -----------------------
    dispositivos_qs = Dispositivo.objects.all()
    dispositivos_vencidos = []
    dispositivos_proximos = []

    for d in dispositivos_qs:
        if not (d.data_ultima_calibracao and d.frequencia_calibracao):
            continue
        prox = _eom(d.data_ultima_calibracao + relativedelta(months=d.frequencia_calibracao))
        setattr(d, "proxima_calibracao", prox)
        if prox < today:
            dispositivos_vencidos.append(d)
        elif today <= prox <= range_end:
            dispositivos_proximos.append(d)

    conjuntos = {
        "vencida": {
            "equipamentos": equipamentos_vencidos,
            "dispositivos": dispositivos_vencidos,
            "alerta_in_app": "MANUTENCAO_VENCIDA",
            "mensagem": "está com a calibração vencida",
            "template": "alertas/calibracao_vencida.html",
        },
        "proxima": {
            "equipamentos": equipamentos_proximos,
            "dispositivos": dispositivos_proximos,
            "alerta_in_app": "MANUTENCAO_PROXIMA",
            "mensagem": "está com a calibração próxima do vencimento",
            "template": "alertas/calibracao_proxima.html",
        },
    }

    for chave, dados in conjuntos.items():
        # Config de e-mail (opcional, via tabela Alerta: 'vencida' | 'proxima')
        try:
            alerta_email = Alerta.objects.get(nome=chave)
        except Alerta.DoesNotExist:
            alerta_email = None

        # Config de alerta in-app
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
                "proxima_calibracao": getattr(dispositivo, "proxima_calibracao", None),
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
                    fail_silently=True,
                )

            # In-app
            for user in destinatarios_in_app:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo="📟 Calibração de Dispositivo Vencida" if chave == "vencida" else "🕒 Calibração de Dispositivo Próxima",
                    mensagem=f"O dispositivo {nome} {dados['mensagem']}.",
                    tipo=dados["alerta_in_app"],
                    referencia_id=dispositivo.id,
                    url_destino=f"/metrologia/dispositivos/{dispositivo.id}/visualizar/",
                )

        # Equipamentos (apenas ativos já filtrados acima)
        for equipamento in dados["equipamentos"]:
            nome = f"{equipamento.codigo} – {equipamento.nome_equipamento}"
            context = {
                "objeto": equipamento,
                "proxima_calibracao": getattr(equipamento, "proxima_calibracao", None),
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
                    fail_silently=True,
                )

            # In-app
            for user in destinatarios_in_app:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo="🔩 Calibração de Equipamento Vencida" if chave == "vencida" else "🕒 Calibração de Equipamento Próxima",
                    mensagem=f"O equipamento {nome} {dados['mensagem']}.",
                    tipo=dados["alerta_in_app"],
                    referencia_id=equipamento.id,
                    url_destino=f"/metrologia/tabelatecnica/{equipamento.id}/visualizar/",
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


# alerts/tasks.py
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.urls import reverse

from alerts.models import AlertaConfigurado, AlertaUsuario
from comercial.models.precalculo import PreCalculo  # ← já existe no seu app

def _prazo_por_tipo(tipo_raw: str) -> int:
    t = (tipo_raw or "").strip().lower()
    if "estamp" in t:
        return 5
    # mola, aramado e qualquer outro → 3 dias
    return 3

@shared_task
def enviar_alertas_avaliacao_tecnica_pendente():
    today = now().date()

    # Pré-cálculos SEM Avaliação Técnica
    pendentes = (
        PreCalculo.objects
        .select_related("analise_comercial_item__item", "cotacao")
        .filter(avaliacao_tecnica_item__isnull=True)
    )

    try:
        config = AlertaConfigurado.objects.get(tipo="AVALIACAO_TECNICA_PENDENTE", ativo=True)
        destinatarios = set(config.usuarios.all())
        for g in config.grupos.all():
            destinatarios.update(g.user_set.all())
    except AlertaConfigurado.DoesNotExist:
        return  # ninguém configurado para receber

    for p in pendentes:
        # tipo da peça (pode não existir se a Análise Comercial ainda não tiver item definido)
        item = getattr(getattr(p, "analise_comercial_item", None), "item", None)
        tipo_peca = getattr(item, "tipo_de_peca", "") or ""
        prazo = _prazo_por_tipo(tipo_peca)

        data_limite = p.criado_em.date() + timedelta(days=prazo)
        if today <= data_limite:
            continue  # ainda no prazo

        dias_atraso = (today - data_limite).days

        # Link para abrir direto na aba de Avaliação Técnica
        try:
            path = reverse("editar_precaculo", args=[p.id]) + "?aba=avali"
        except Exception:
            path = reverse("itens_precaculo", args=[p.cotacao_id])
        base = getattr(settings, "SITE_URL", "").rstrip("/")
        link_abs = f"{base}{path}" if base else path

        ctx = {
            "precalculo": p,
            "cotacao": p.cotacao,
            "item": item,
            "tipo_de_peca": tipo_peca or "—",
            "prazo_dias": prazo,
            "data_limite": data_limite,
            "dias_atraso": dias_atraso,
            "link": link_abs,
        }

        subject = render_to_string("alertas/precalc_avaliacao_pendente_assunto.txt", ctx).strip()
        text    = render_to_string("alertas/precalc_avaliacao_pendente.txt",    ctx)
        html    = render_to_string("alertas/precalc_avaliacao_pendente.html",   ctx)

        for user in destinatarios:
            # Evita duplicar no mesmo dia por usuário+precalc
            ja_notificado = AlertaUsuario.objects.filter(
                usuario=user,
                tipo="AVALIACAO_TECNICA_PENDENTE",
                referencia_id=p.id,
                criado_em__date=today,
            ).exists()
            if ja_notificado:
                continue

            # In-app
            AlertaUsuario.objects.create(
                usuario=user,
                titulo=subject,
                mensagem=text,
                tipo="AVALIACAO_TECNICA_PENDENTE",
                referencia_id=p.id,
                url_destino=path,
            )

            # E-mail (se existir)
            if user.email:
                send_mail(
                    subject=subject,
                    message=text,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@brasmol.com.br"),
                    recipient_list=[user.email],
                    html_message=html,
                    fail_silently=True,
                )
