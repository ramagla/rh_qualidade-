from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from portaria.models.ocorrencia import OcorrenciaPortaria
from portaria.forms.ocorrencia_form import OcorrenciaPortariaForm
from django.contrib import messages
from django.utils.timezone import now
from django.core.paginator import Paginator

from django.db.models import Q

@login_required
@permission_required("portaria.view_ocorrenciaportaria", raise_exception=True)
def listar_ocorrencias(request):
    ocorrencias_queryset = OcorrenciaPortaria.objects.select_related("responsavel_registro").filter(
        pessoas_envolvidas__status="Ativo"
    ).distinct().order_by("-data_inicio", "-hora_inicio")

    tipo = request.GET.get("tipo")
    status = request.GET.get("status")
    data = request.GET.get("data")

    if tipo:
        ocorrencias_queryset = ocorrencias_queryset.filter(tipo_ocorrencia=tipo)
    if status:
        ocorrencias_queryset = ocorrencias_queryset.filter(status=status)
    if data:
        ocorrencias_queryset = ocorrencias_queryset.filter(data_inicio=data)

    total_abertas = ocorrencias_queryset.filter(status="aberta").count()
    total_analise = ocorrencias_queryset.filter(status="analise").count()
    total_encerradas = ocorrencias_queryset.filter(status="encerrada").count()

    paginator = Paginator(ocorrencias_queryset, 10)
    pagina = request.GET.get("page")
    page_obj = paginator.get_page(pagina)

    context = {
        "ocorrencias": page_obj,
        "page_obj": page_obj,
        "total_abertas": total_abertas,
        "total_analise": total_analise,
        "total_encerradas": total_encerradas,
    }

    return render(request, "ocorrencias/lista_ocorrencias.html", context)




@login_required
@permission_required("portaria.add_ocorrenciaportaria", raise_exception=True)
def cadastrar_ocorrencia(request):
    if request.method == "POST":
        form = OcorrenciaPortariaForm(request.POST, request.FILES)
        if form.is_valid():
            ocorrencia = form.save(commit=False)
            ocorrencia.responsavel_registro = request.user
            ocorrencia.save()
            form.save_m2m()
            disparar_alerta_ocorrencia(request, ocorrencia.pk, edicao=False)
            messages.success(request, "Ocorrência registrada com sucesso.")
            return redirect("listar_ocorrencias")
    else:
        form = OcorrenciaPortariaForm()
    return render(request, "ocorrencias/form_ocorrencias.html", {"form": form})


@login_required
@permission_required("portaria.change_ocorrenciaportaria", raise_exception=True)
def editar_ocorrencia(request, pk):
    ocorrencia = get_object_or_404(OcorrenciaPortaria, pk=pk)
    if request.method == "POST":
        form = OcorrenciaPortariaForm(request.POST, request.FILES, instance=ocorrencia)
        if form.is_valid():
            ocorrencia = form.save(commit=False)
            ocorrencia.responsavel_registro = request.user
            ocorrencia.save()
            form.save_m2m()
            disparar_alerta_ocorrencia(request, ocorrencia.pk, edicao=True)
            messages.success(request, "Ocorrência atualizada com sucesso.")
            return redirect("listar_ocorrencias")
    else:
        form = OcorrenciaPortariaForm(instance=ocorrencia)
    return render(request, "ocorrencias/form_ocorrencias.html", {"form": form, "ocorrencia": ocorrencia})



from django.utils.timezone import now

@login_required
@permission_required("portaria.view_ocorrenciaportaria", raise_exception=True)
def visualizar_ocorrencia(request, pk):
    ocorrencia = get_object_or_404(OcorrenciaPortaria, pk=pk)
    return render(
        request,
        "ocorrencias/visualizar_ocorrencia.html",
        {
            "ocorrencia": ocorrencia,
            "now": now(),  # ✅ necessário para uso no template
        }
    )


@login_required
@permission_required("portaria.delete_ocorrenciaportaria", raise_exception=True)
def excluir_ocorrencia(request, pk):
    ocorrencia = get_object_or_404(OcorrenciaPortaria, pk=pk)
    if request.method == "POST":
        ocorrencia.delete()
        messages.success(request, "Ocorrência excluída com sucesso.")
        return redirect("listar_ocorrencias")
    return render(request, "ocorrencias/excluir_confirmacao.html", {"ocorrencia": ocorrencia})

from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.timezone import now

from alerts.models import AlertaUsuario
from portaria.models.ocorrencia import OcorrenciaPortaria

@login_required
@permission_required("portaria.change_ocorrenciaportaria", raise_exception=True)
def disparar_alerta_ocorrencia(request, pk, edicao=False):
    ocorrencia = get_object_or_404(OcorrenciaPortaria, pk=pk)

    envolvidos = ocorrencia.pessoas_envolvidas.filter(user__isnull=False, status="Ativo")

    if not envolvidos.exists():
        messages.error(request, "Nenhum dos envolvidos possui usuário vinculado.")
        return redirect("listar_ocorrencias")

    for funcionario in envolvidos:
        user_destino = funcionario.user

        # Alerta in-app
        AlertaUsuario.objects.create(
            usuario=user_destino,
            titulo="🚨 Ocorrência Atualizada" if edicao else "🚨 Você foi citado em uma Ocorrência",
            mensagem=f"A ocorrência do tipo '{ocorrencia.get_tipo_ocorrencia_display()}' foi {'atualizada' if edicao else 'registrada'} no sistema.",
            tipo="ocorrencia",
            referencia_id=ocorrencia.id,
            url_destino=f"/portaria/ocorrencias/visualizar/{ocorrencia.id}/",
        )

        # E-mail
        html_email = render_to_string(
            "emails/ocorrencia_alerta_email.html",
            {
                "ocorrencia": ocorrencia,
                "destinatario": funcionario,
                "ano": now().year,
                "edicao": edicao,
            }
        )

        send_mail(
            subject="🚨 Ocorrência Atualizada" if edicao else "🚨 Alerta de Ocorrência",
            message=f"Você foi citado em uma ocorrência {'atualizada' if edicao else 'registrada'}.",
            from_email="no-reply@brasmol.com.br",
            recipient_list=[user_destino.email],
            html_message=html_email,
            fail_silently=True,
        )

    messages.success(request, "Alerta enviado para todos os envolvidos.")
    return redirect("listar_ocorrencias")
