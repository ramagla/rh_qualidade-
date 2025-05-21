from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from portaria.forms.veiculo_form import VeiculoPortariaForm
from portaria.models import VeiculoPortaria
from django.core.paginator import Paginator


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from portaria.models import VeiculoPortaria

from django.db.models import F

from portaria.models.pessoas import PessoaPortaria

@login_required
def lista_veiculos(request):
    veiculos = VeiculoPortaria.objects.select_related('pessoa').all().order_by("placa")

    # Filtros
    placa = request.GET.get("placa")
    tipo = request.GET.get("tipo")
    pessoa_nome = request.GET.get("pessoa")

    if placa:
        veiculos = veiculos.filter(placa=placa)

    if tipo:
        veiculos = veiculos.filter(tipo=tipo)

    if pessoa_nome:
        veiculos = veiculos.filter(pessoa__nome=pessoa_nome)

    # Indicadores
    total_veiculos = veiculos.count()
    total_com_pessoa = veiculos.filter(pessoa__isnull=False).count()
    total_sem_pessoa = veiculos.filter(pessoa__isnull=True).count()

    # Listas dinâmicas para selects
    placas_disponiveis = VeiculoPortaria.objects.order_by("placa").values_list("placa", flat=True).distinct()
    pessoas_disponiveis = PessoaPortaria.objects.filter(veiculos_individuais__isnull=False).distinct().order_by("nome")

    # Paginação
    paginator = Paginator(veiculos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    tipos = VeiculoPortaria.TIPO_CHOICES

    return render(request, "cadastros/lista_veiculos.html", {
        "veiculos": page_obj,
        "page_obj": page_obj,
        "tipos": tipos,
        "placas_disponiveis": placas_disponiveis,
        "pessoas_disponiveis": pessoas_disponiveis,
        "total_veiculos": total_veiculos,
        "total_com_pessoa": total_com_pessoa,
        "total_sem_pessoa": total_sem_pessoa,
    })




@login_required
def cadastrar_veiculo(request):
    form = VeiculoPortariaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        veiculo = form.save()

        # 🔁 Sincroniza com o campo veiculos_vinculados da pessoa
        if veiculo.pessoa:
            veiculo.pessoa.veiculos_vinculados.add(veiculo)

        messages.success(request, "Veículo cadastrado com sucesso!")
        return redirect("lista_veiculos")

    return render(request, "cadastros/form_veiculo.html", {"form": form})


@login_required
def editar_veiculo(request, pk):
    veiculo = get_object_or_404(VeiculoPortaria, pk=pk)
    form = VeiculoPortariaForm(request.POST or None, instance=veiculo)

    if request.method == "POST" and form.is_valid():
        veiculo = form.save()

        # 🔁 Atualiza o vínculo M2M na pessoa
        if veiculo.pessoa:
            veiculo.pessoa.veiculos_vinculados.add(veiculo)

        messages.success(request, "Veículo atualizado com sucesso!")
        return redirect("lista_veiculos")

    return render(request, "cadastros/form_veiculo.html", {"form": form})



from django.shortcuts import get_object_or_404

@login_required
def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(VeiculoPortaria, pk=pk)

    if request.method == "POST":
        veiculo.delete()
        messages.success(request, "Veículo excluído com sucesso.")
        return redirect("lista_veiculos")

    return render(request, "cadastros/confirmar_exclusao_veiculo.html", {"veiculo": veiculo})
