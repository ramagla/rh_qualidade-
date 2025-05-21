from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from portaria.models import PessoaPortaria


# portaria/views/visitante_views.py
from django.utils.timezone import now
from django.shortcuts import render, redirect
from portaria.models import PessoaPortaria, EntradaVisitante, VeiculoPortaria
from portaria.forms.entrada_visitante_form import EntradaVisitanteForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.views.decorators.http import require_POST

@login_required
@permission_required("portaria.change_entradavisitante", raise_exception=True)
@require_POST
def registrar_saida_visitante(request, pk):
    entrada = get_object_or_404(EntradaVisitante, pk=pk)
    hora = request.POST.get("hora_saida")
    if hora:
        entrada.hora_saida = hora
        entrada.save()
        messages.success(request, "Saída registrada com sucesso.")
    else:
        messages.error(request, "Hora de saída inválida.")
    return redirect("listar_controle_visitantes")

@login_required
def registrar_entrada_visitante(request):
    if request.method == "POST":
        form = EntradaVisitanteForm(request.POST, request.FILES)
        if form.is_valid():
            # Se não selecionou pessoa existente, cria nova
            if not form.cleaned_data["pessoa"]:
                nova_pessoa = PessoaPortaria.objects.create(
                    nome=form.cleaned_data["nome"],
                    documento=form.cleaned_data["documento"],
                    empresa=form.cleaned_data["empresa"],
                    tipo="visitante",  # fixo
                    foto=form.cleaned_data["foto"],
                )
                form.instance.pessoa = nova_pessoa

            entrada = form.save()
            messages.success(request, "Entrada registrada com sucesso.")
            return redirect("listar_controle_visitantes")
        else:
            messages.error(request, "Erro ao registrar entrada. Verifique os campos.")
    else:
        form = EntradaVisitanteForm(initial={"data": now().date(), "hora_entrada": now().time()})

    return render(request, "portaria/entrada_visitante_form.html", {"form": form})



# portaria/views/controle_visitantes_views.py
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.timezone import now
from portaria.models import EntradaVisitante

@login_required
def listar_controle_visitantes(request):
    visitas = EntradaVisitante.objects.select_related("pessoa", "veiculo").order_by("-data", "-hora_entrada")

    # Filtros GET
    nome_filtro = request.GET.get("nome")
    data_filtro = request.GET.get("data")
    motivo_filtro = request.GET.get("motivo")

    if nome_filtro:
        visitas = visitas.filter(pessoa__nome=nome_filtro)
    if data_filtro:
        visitas = visitas.filter(data=data_filtro)
    if motivo_filtro:
        visitas = visitas.filter(motivo=motivo_filtro)

    # Indicadores
    total_registros = visitas.count()
    total_hoje = EntradaVisitante.objects.filter(data=now().date()).count()
    total_pendentes = EntradaVisitante.objects.filter(hora_saida__isnull=True).count()

    # Paginação
    paginator = Paginator(visitas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtros dinâmicos
    nomes_disponiveis = EntradaVisitante.objects.values_list("pessoa__nome", flat=True).distinct().order_by("pessoa__nome")
    motivos = EntradaVisitante._meta.get_field("motivo").choices

    return render(
        request,
        "visitantes/controle_visitantes_lista.html",
        {
            "visitas": page_obj,
            "page_obj": page_obj,
            "total_registros": total_registros,
            "total_hoje": total_hoje,
            "total_pendentes": total_pendentes,
            "nomes_disponiveis": nomes_disponiveis,
            "motivos": motivos,
        }
    )


# portaria/views/controle_visitantes_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.timezone import now

from portaria.models import PessoaPortaria, EntradaVisitante, VeiculoPortaria
from portaria.forms.entrada_visitante_form import EntradaVisitanteForm


from django.core.files.base import ContentFile
import base64
import uuid
from django.db.models import Q

@login_required
@permission_required("portaria.add_entradavisitante", raise_exception=True)
def cadastrar_entrada_visitante(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        if post_data.get("pessoa") == "novo":
            post_data["pessoa"] = ""

        form = EntradaVisitanteForm(post_data, request.FILES)

        if form.is_valid():
            pessoa = form.cleaned_data.get("pessoa")
            tipo = form.cleaned_data.get("tipo")
            nome = form.cleaned_data.get("nome")
            documento = form.cleaned_data.get("documento")
            empresa = form.cleaned_data.get("empresa")
            foto = form.cleaned_data.get("foto")
            veiculo_manual = request.POST.get("veiculo_manual")
            tipo_veiculo = form.cleaned_data.get("tipo_veiculo")

            # 📸 Foto base64
            foto_base64 = request.POST.get("foto")
            if not foto and foto_base64:
                try:
                    format, imgstr = foto_base64.split(';base64,')
                    ext = format.split('/')[-1]
                    file_name = f"{uuid.uuid4().hex}.{ext}"
                    foto = ContentFile(base64.b64decode(imgstr), name=file_name)
                except Exception:
                    foto = None

            # 🔒 Verificações de duplicidade
            if not pessoa:
                if documento and PessoaPortaria.objects.filter(documento=documento).exists():
                    messages.error(request, "Já existe uma pessoa cadastrada com este RG.")
                    return render(request, "visitantes/entrada_visitante_form.html", {
                        "form": form,
                        "pessoas": PessoaPortaria.objects.filter(tipo__in=["visitante", "entregador"]).order_by("nome"),
                        "edicao": False
                    })

                if veiculo_manual and VeiculoPortaria.objects.filter(placa__iexact=veiculo_manual).exists():
                    messages.error(request, "Já existe um veículo com esta placa cadastrado.")
                    return render(request, "visitantes/entrada_visitante_form.html", {
                        "form": form,
                        "pessoas": PessoaPortaria.objects.filter(tipo__in=["visitante", "entregador"]).order_by("nome"),
                        "edicao": False
                    })

                # Criar nova pessoa
                nova_pessoa = PessoaPortaria.objects.create(
                    nome=nome,
                    documento=documento,
                    empresa=empresa,
                    tipo=tipo or "visitante",
                    foto=foto,
                )
                form.instance.pessoa = nova_pessoa

                # Criar veículo
                if veiculo_manual:
                    veiculo = VeiculoPortaria.objects.create(
                        pessoa=nova_pessoa,
                        placa=veiculo_manual.upper(),
                        tipo=tipo_veiculo or "outro",
                    )
                    form.instance.veiculo = veiculo
                    nova_pessoa.veiculos_vinculados.add(veiculo)

            else:
                form.instance.pessoa = pessoa

            form.save()
            messages.success(request, "Entrada registrada com sucesso.")
            return redirect("listar_controle_visitantes")
        else:
            messages.error(request, "Erro ao registrar entrada. Verifique os campos.")

    else:
        form = EntradaVisitanteForm(initial={
            "data": now().date(),
            "hora_entrada": datetime.now().strftime("%H:%M")
        })
    pessoas = PessoaPortaria.objects.filter(tipo__in=["visitante", "entregador"]).order_by("nome")
    return render(request, "visitantes/entrada_visitante_form.html", {
        "form": form,
        "pessoas": pessoas,
        "edicao": False
    })




@login_required
@permission_required("portaria.change_entradavisitante", raise_exception=True)
def editar_entrada_visitante(request, pk):
    entrada = get_object_or_404(EntradaVisitante, pk=pk)
    form = EntradaVisitanteForm(request.POST or None, request.FILES or None, instance=entrada)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Entrada atualizada com sucesso.")
            return redirect("listar_controle_visitantes")
        else:
            messages.error(request, "Erro ao atualizar. Verifique os campos.")

    pessoas = PessoaPortaria.objects.filter(tipo__in=["visitante", "entregador"]).order_by("nome")
    return render(request, "visitantes/entrada_visitante_form.html", {
        "form": form,
        "pessoas": pessoas,
        "edicao": True
    })

@login_required
@permission_required("portaria.view_entradavisitante", raise_exception=True)
def visualizar_entrada_visitante(request, pk):
    entrada = get_object_or_404(EntradaVisitante, pk=pk)

    permanencia = None
    if entrada.hora_entrada and entrada.hora_saida:
        h_entrada = datetime.combine(entrada.data, entrada.hora_entrada)
        h_saida = datetime.combine(entrada.data, entrada.hora_saida)
        duracao = h_saida - h_entrada
        permanencia = str(duracao).split('.')[0]

    return render(
        request,
        "visitantes/entrada_visitante_visualizar.html",
        {
            "entrada": entrada,
            "permanencia": permanencia,
            "now": now(),
        }
    )


@login_required
@permission_required("portaria.delete_entradavisitante", raise_exception=True)
def excluir_entrada_visitante(request, pk):
    entrada = get_object_or_404(EntradaVisitante, pk=pk)
    entrada.delete()
    messages.success(request, "Entrada excluída com sucesso.")
    return redirect("listar_controle_visitantes")

from django.http import JsonResponse
from django.conf import settings

@login_required
def obter_foto_pessoa(request, pk):
    pessoa = get_object_or_404(PessoaPortaria, pk=pk)
    if pessoa.foto:
        return JsonResponse({"foto_url": pessoa.foto.url})
    return JsonResponse({"foto_url": None})