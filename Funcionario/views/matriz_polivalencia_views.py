from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator


# Configurar o backend antes de importar pyplot
import matplotlib
matplotlib.use('Agg')  # Backend para renderização sem GUI
import matplotlib.pyplot as plt

import io
import base64

from ..models.matriz_polivalencia import MatrizPolivalencia, Atividade, Nota
from ..models.funcionario import Funcionario
from ..forms.matriz_polivalencia_forms import MatrizPolivalenciaForm, AtividadeForm, NotaForm

def lista_matriz_polivalencia(request):
    departamento = request.GET.get('departamento')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Filtrando as matrizes
    matrizes = MatrizPolivalencia.objects.all()

    # Filtrando matrizes por departamento
    if departamento:
        matrizes = matrizes.filter(departamento=departamento)

   

    # Filtro de datas
    if data_inicio:
        matrizes = matrizes.filter(atualizado_em__gte=data_inicio)

    if data_fim:
        matrizes = matrizes.filter(atualizado_em__lte=data_fim)

    # Recuperando os departamentos disponíveis
    departamentos = MatrizPolivalencia.objects.values_list('departamento', flat=True).distinct()

    # Paginação
    paginator = Paginator(matrizes, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request, 'matriz_polivalencia/matriz_polivalencia_lista.html', {
        'matrizes': page_obj,
        'page_obj': page_obj,
        'departamentos': departamentos
    })



def gerar_grafico_icone(nota):    
    icones = {
        0: "icons/barra_0.png",
        1: "icons/barra_1.png",
        2: "icons/barra_2.png",
        3: "icons/barra_3.png",
        4: "icons/barra_4.png",
    }
    return icones.get(nota, "icons/barra_1.png")


def imprimir_matriz(request, **kwargs):
    id = kwargs.get("id")
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    atividades = matriz.atividades
    colaboradores = matriz.funcionarios

    # Construir o dicionário de notas com suplente
    notas_por_funcionario = {}
    for colaborador in colaboradores:
        notas_por_funcionario[colaborador.id] = {
            atividade.id: {"pontuacao": None, "suplente": False, "grafico": None}
            for atividade in atividades
        }

    for nota in Nota.objects.filter(funcionario__in=colaboradores, atividade__in=atividades):
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "suplente": nota.suplente,
            "grafico": gerar_grafico_icone(nota.pontuacao),  # Usa o ícone com base na pontuação
        }

    # Transformar para lista plana para uso no template
    notas_lista = [
        {
            "colaborador_id": colab_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "suplente": valores["suplente"],
            "grafico": valores["grafico"],
        }
        for colab_id, atividades in notas_por_funcionario.items()
        for ativ_id, valores in atividades.items()
    ]

    # Adicionar status de suplente para cada colaborador
    colaboradores_com_suplente = [
        {
            "id": colaborador.id,
            "nome": colaborador.nome,
            "suplente": any(
                nota["suplente"] for nota in notas_por_funcionario[colaborador.id].values()
            ),
        }
        for colaborador in colaboradores
    ]

    # Adicionar dados ao contexto para renderizar o template
    context = {
        "matriz": matriz,
        "atividades": atividades,
        "colaboradores": colaboradores_com_suplente,
        "notas_lista": notas_lista,
    }

    return render(request, "matriz_polivalencia/imprimir_matriz.html", context)


def cadastrar_matriz_polivalencia(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")  # Funcionários ativos ordenados
    atividades = Atividade.objects.all()  # Todas as atividades
    departamentos = Atividade.objects.values_list("departamento", flat=True).distinct()  # Departamentos únicos

    if request.method == 'POST':
        form = MatrizPolivalenciaForm(request.POST)
        if form.is_valid():
            matriz = form.save()

            # Processa as notas e suplentes dos funcionários
            for funcionario in funcionarios:
                for atividade in atividades:
                    nota_key = f"nota_{funcionario.id}_{atividade.id}"
                    suplente_key = f"suplente_{funcionario.id}"
                    nota_value = request.POST.get(nota_key)

                    # Converter nota para número inteiro e validar
                    nota_value = int(nota_value) if nota_value is not None and nota_value.isdigit() else None
                    suplente_value = request.POST.get(suplente_key, "off") == "on"

                    if nota_value is not None:  # Verifica se a nota foi fornecida, incluindo 0
                        Nota.objects.update_or_create(
                            funcionario=funcionario,
                            atividade=atividade,
                            defaults={"pontuacao": nota_value, "suplente": suplente_value},
                        )

            messages.success(request, "Matriz de Polivalência cadastrada com sucesso!")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(request, "Erro ao cadastrar a Matriz de Polivalência. Verifique os dados.")
    else:
        form = MatrizPolivalenciaForm()

    return render(request, 'matriz_polivalencia/cadastrar_matriz.html', {
        'form': form,
        'funcionarios': funcionarios,
        'atividades': atividades,
        'departamentos': departamentos,
    })



# Editar uma matriz de polivalência
def editar_matriz_polivalencia(request, id):
    # Pré-carregar as relações para otimizar o acesso aos dados relacionados
    matriz = get_object_or_404(
        MatrizPolivalencia.objects.select_related("elaboracao", "coordenacao", "validacao"), id=id
    )

    # Obter lista de funcionários ativos
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    # Obter todos os departamentos
    departamentos = Atividade.objects.values_list("departamento", flat=True).distinct()

    # Departamento fixo associado ao cadastro da matriz
    departamento_selecionado = matriz.departamento

    # Filtrar atividades relacionadas ao departamento selecionado
    atividades = Atividade.objects.filter(departamento=departamento_selecionado)

    # Construir o dicionário de notas com suplente
    notas_por_funcionario = {}
    for funcionario in funcionarios:
        notas_por_funcionario[funcionario.id] = {
            atividade.id: {"pontuacao": None, "suplente": False}
            for atividade in atividades
        }

    # Preencher com os valores das notas existentes
    for nota in Nota.objects.filter(funcionario__in=funcionarios, atividade__in=atividades):
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "suplente": nota.suplente,
        }

    if request.method == "POST":
        # Processar o formulário com os dados enviados
        form = MatrizPolivalenciaForm(request.POST, instance=matriz)
        if form.is_valid():
            matriz = form.save(commit=False)
            
            # Certificar que o departamento não seja sobrescrito ou apagado
            matriz.departamento = departamento_selecionado
            matriz.save()

            # Atualizar as notas com os valores do POST
            for funcionario in funcionarios:
                for atividade in atividades:
                    nota_key = f"nota_{funcionario.id}_{atividade.id}"
                    suplente_key = f"suplente_{funcionario.id}"
                    nota_value = request.POST.get(nota_key)
                    suplente_value = request.POST.get(suplente_key, "off") == "on"

                    if nota_value:  # Se uma nota foi fornecida
                        Nota.objects.update_or_create(
                            funcionario=funcionario,
                            atividade=atividade,
                            defaults={"pontuacao": nota_value, "suplente": suplente_value},
                        )

            messages.success(request, "Matriz de Polivalência atualizada com sucesso.")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(request, "Erro ao atualizar a Matriz de Polivalência. Verifique os dados.")
    else:
        # Instanciar o formulário com a matriz existente
        form = MatrizPolivalenciaForm(instance=matriz)

    # Preparar o contexto com notas em formato acessível ao template
    notas_lista = [
        {
            "funcionario_id": func_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "suplente": valores["suplente"],
        }
        for func_id, atividades in notas_por_funcionario.items()
        for ativ_id, valores in atividades.items()
    ]

    # Retornar o template de edição com todos os dados necessários
    return render(request, "matriz_polivalencia/editar_matriz.html", {
        "form": form,
        "matriz": matriz,
        "funcionarios": funcionarios,
        "atividades": atividades,
        "departamentos": departamentos,
        "notas_lista": notas_lista,
        "departamento_selecionado": departamento_selecionado,  # Informação fixa do departamento
    })





# Excluir uma matriz de polivalência
def excluir_matriz_polivalencia(request, id):
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    if request.method == "POST":
        matriz.delete()  # O método sobrescrito cuidará de excluir as notas relacionadas
        messages.success(request, "Matriz de Polivalência e suas notas relacionadas foram excluídas com sucesso.")
        return redirect('lista_matriz_polivalencia')
    return render(request, 'matriz_polivalencia/excluir.html', {'matriz': matriz})


def lista_atividades(request):
    # Pega os filtros do GET
    departamento = request.GET.get('departamento', '')
    nome = request.GET.get('nome', '')
   
    # Filtrando as atividades
    atividades = Atividade.objects.all()

    if departamento:
        atividades = atividades.filter(departamento=departamento)

    if nome:
        atividades = atividades.filter(nome__icontains=nome)

    # Adicionando uma ordenação para evitar o erro de "UnorderedObjectListWarning"
    atividades = atividades.order_by('nome')  # Ou qualquer outro campo desejado

    # Paginação
    paginator = Paginator(atividades, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para os cards e acordions
    total_atividades = atividades.count()
    
    # Quantidade de atividades por departamento
    atividades_por_departamento = (
        Atividade.objects.values('departamento')
        .annotate(total=Count('departamento'))
        .order_by('departamento')
    )


    return render(request, 'matriz_polivalencia/lista_atividades.html', {
        'page_obj': page_obj,  # Objeto de paginação
        'nomes_atividades': Atividade.objects.values_list('nome', flat=True).distinct(),  # Listagem de nomes para filtro
        'departamentos': Atividade.objects.values_list('departamento', flat=True).distinct(),  # Listagem de departamentos para filtro
        'total_atividades': total_atividades,  # Total de atividades
        'atividades_por_departamento': atividades_por_departamento,  # Atividades por departamento
    })
    
def cadastrar_atividade(request):
    # Obter todos os departamentos únicos
    departamentos = Funcionario.objects.values('local_trabalho').distinct()

    # Obter todos os funcionários ativos
    funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')  

    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade cadastrada com sucesso!")
            return redirect('lista_atividades')  
    else:
        form = AtividadeForm()

    return render(request, 'matriz_polivalencia/cadastrar_atividade.html', {
        'form': form,
        'funcionarios': funcionarios,  # Passa os funcionários para o template
        'departamentos': departamentos  # Passa os departamentos únicos para o template
    })

# Gerenciar notas (adicionar/editar/excluir)
def gerenciar_notas(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    if request.method == "POST":
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.atividade = atividade
            nota.save()
            messages.success(request, "Nota adicionada/atualizada com sucesso.")
            return redirect('visualizar_matriz_polivalencia', id=atividade.departamento)
    else:
        form = NotaForm()
    notas = atividade.notas.all()
    return render(request, 'matriz_polivalencia/gerenciar_notas.html', {
        'form': form,
        'notas': notas,
        'atividade': atividade,
    })





def visualizar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    return render(request, 'matriz_polivalencia/visualizar_atividade.html', {'atividade': atividade})


def editar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    departamentos = Funcionario.objects.values('local_trabalho').distinct()  # Lista de departamentos únicos

    if request.method == "POST":
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade atualizada com sucesso.")
            return redirect('lista_atividades')
    else:
        form = AtividadeForm(instance=atividade)

    return render(request, 'matriz_polivalencia/editar_atividade.html', {
        'form': form,
        'atividade': atividade,
        'departamentos': departamentos,  # Passa os departamentos como contexto
    })



def excluir_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    if request.method == "POST":
        atividade.delete()
        messages.success(request, "Atividade excluída com sucesso.")
        return redirect('lista_atividades')  # Redireciona para a lista de atividades
    return render(request, 'matriz_polivalencia/excluir_atividade.html', {'atividade': atividade})

def get_atividades_por_departamento(request):
    departamento = request.GET.get('departamento')  # Obtém o departamento selecionado
    atividades = Atividade.objects.filter(departamento=departamento)  # Filtra atividades pelo departamento
    atividade_list = [{'id': atividade.id, 'nome': atividade.nome} for atividade in atividades]
    return JsonResponse({'atividades': atividade_list})


def get_atividades_e_funcionarios_por_departamento(request):
    departamento = request.GET.get('departamento')

    if departamento:
        # Obter as atividades associadas ao departamento
        atividades = Atividade.objects.filter(departamento=departamento).values('id', 'nome')

        # Obter todos os funcionários ativos, ordenados alfabeticamente
        funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome').values('id', 'nome')

        # Retornar as atividades e funcionários em formato JSON
        return JsonResponse({
            'atividades': list(atividades),
            'funcionarios': list(funcionarios)
        })

    return JsonResponse({'error': 'Departamento não encontrado'}, status=400)