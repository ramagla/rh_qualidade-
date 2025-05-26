from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from portaria.forms.pessoa_form import PessoaPortariaForm

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from ..models import PessoaPortaria
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
import base64
from django.core.files.base import ContentFile

@login_required
def lista_pessoas(request):
    pessoas = PessoaPortaria.objects.all().order_by("nome")

    # Indicadores
    total_pessoas = pessoas.count()
    visitantes = pessoas.filter(tipo="visitante").count()
    entregadores = pessoas.filter(tipo="entregador").count()
    colaboradores = pessoas.filter(tipo="colaborador").count()

      # Filtros GET
    nome_filtro = request.GET.get("nome")
    tipo_filtro = request.GET.get("tipo")
    empresa_filtro = request.GET.get("empresa")

    if nome_filtro:
        pessoas = pessoas.filter(nome=nome_filtro)
    if tipo_filtro:
        pessoas = pessoas.filter(tipo=tipo_filtro)
    if empresa_filtro:
        pessoas = pessoas.filter(empresa=empresa_filtro)

    # Paginação
    paginator = Paginator(pessoas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Listas únicas para os filtros
    nomes_disponiveis = PessoaPortaria.objects.order_by("nome").values_list("nome", flat=True).distinct()
    empresas_disponiveis = PessoaPortaria.objects.exclude(empresa__isnull=True).exclude(empresa="").order_by("empresa").values_list("empresa", flat=True).distinct()


    return render(
        request,
        "cadastros/lista_pessoas.html",
        {
            "pessoas": page_obj,
            "page_obj": page_obj,
            "total_pessoas": total_pessoas,
            "visitantes": visitantes,
            "entregadores": entregadores,
            "colaboradores": colaboradores,
            "tipos": PessoaPortaria.TIPOS,
            "nomes_disponiveis": nomes_disponiveis,
            "empresas_disponiveis": empresas_disponiveis,
        }
    )


@login_required
def cadastrar_pessoa(request):
    form = PessoaPortariaForm(request.POST, request.FILES)
    if request.method == "POST":
        if form.is_valid():
            pessoa = form.save(commit=False)

            # foto base64 (como já faz)
            foto_base64 = request.POST.get("foto_base64")
            if foto_base64 and foto_base64.startswith("data:image"):
                format, imgstr = foto_base64.split(";base64,")
                ext = format.split("/")[-1]
                img_data = ContentFile(base64.b64decode(imgstr), name=f"foto_{pessoa.nome.replace(' ', '_')}.{ext}")
                pessoa.foto = img_data

            pessoa.save()
            form.save_m2m()

            # 🔁 Atualizar os veículos vinculados
            for veiculo in form.cleaned_data.get("veiculos_vinculados", []):
                veiculo.pessoa = pessoa
                veiculo.save()

            messages.success(request, "Pessoa cadastrada com sucesso!")
            return redirect("lista_pessoas")
        else:
            messages.error(request, "Erro ao salvar. Verifique os campos.")

    return render(request, "cadastros/form_pessoa.html", {"form": form})



@login_required
def editar_pessoa(request, pk):
    pessoa = get_object_or_404(PessoaPortaria, pk=pk)
    form = PessoaPortariaForm(request.POST or None, request.FILES or None, instance=pessoa)

    if request.method == "POST":
        if form.is_valid():
            pessoa = form.save(commit=False)

            foto_base64 = request.POST.get("foto_base64")
            if foto_base64 and foto_base64.startswith("data:image"):
                format, imgstr = foto_base64.split(";base64,")
                ext = format.split("/")[-1]
                img_data = ContentFile(base64.b64decode(imgstr), name=f"foto_{pessoa.nome.replace(' ', '_')}.{ext}")
                pessoa.foto = img_data

            pessoa.save()
            form.save_m2m()

            for veiculo in form.cleaned_data.get("veiculos_vinculados", []):
                veiculo.pessoa = pessoa
                veiculo.save()
            messages.success(request, "Pessoa atualizada com sucesso!")
            return redirect("lista_pessoas")
        else:
            messages.error(request, "Erro ao atualizar. Verifique os campos.")

    return render(request, "cadastros/form_pessoa.html", {"form": form})

from django.utils.timezone import now

@login_required
@permission_required("Portaria.view_pessoaportaria", raise_exception=True)
def visualizar_pessoa(request, pk):
    pessoa = get_object_or_404(PessoaPortaria, pk=pk)
    return render(
        request,
        "cadastros/pessoa_visualizar.html",
        {
            "pessoa": pessoa,
            "now": now(),  # ✅ adiciona data/hora atual ao contexto
        }
    )


@login_required
@permission_required("Portaria.delete_pessoaportaria", raise_exception=True)
def excluir_pessoa(request, pk):
    pessoa = get_object_or_404(PessoaPortaria, pk=pk)
    if request.method == "POST":
        pessoa.delete()
        messages.success(request, "Pessoa excluída com sucesso.")
        return redirect("lista_pessoas")
    return render(request, "portaria/pessoa_confirmar_exclusao.html", {"pessoa": pessoa})
