# Django
from django.db.models import Q

# App Interno
from Funcionario.models import Funcionario, IntegracaoFuncionario


def filtrar_integracoes(request):
    """Aplica os filtros fornecidos na requisição para o queryset de integrações."""
    queryset = IntegracaoFuncionario.objects.all()

    funcionario_id = request.GET.get("funcionario")
    departamento_id = request.GET.get("departamento")
    requer_treinamento = request.GET.get("requer_treinamento")
    grupo_whatsapp = request.GET.get("grupo_whatsapp")

    if funcionario_id:
        queryset = queryset.filter(funcionario_id=funcionario_id)

    if departamento_id and departamento_id != "None":
        queryset = queryset.filter(funcionario__local_trabalho__nome=departamento_id)

    if requer_treinamento:
        queryset = queryset.filter(requer_treinamento=(requer_treinamento == "True"))

    if grupo_whatsapp:
        queryset = queryset.filter(grupo_whatsapp=(grupo_whatsapp == "True"))

    return queryset.order_by("funcionario__nome")


def obter_contexto_lista_integracoes(request, queryset):
    """Gera o contexto com filtros, dados paginados e contagens para a listagem."""
    from django.core.paginator import Paginator

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    funcionarios = (
        Funcionario.objects.filter(integracaofuncionario__isnull=False)
        .distinct()
        .order_by("nome")
    )

    departamentos = (
        Funcionario.objects.filter(integracaofuncionario__isnull=False)
        .values_list("local_trabalho__nome", flat=True)
        .distinct()
        .order_by("local_trabalho__nome")
    )

    return {
        "integracoes": page_obj,
        "page_obj": page_obj,
        "funcionarios": funcionarios,
        "departamentos": departamentos,
        "total_integracoes": queryset.count(),
        "total_requer_treinamento": queryset.filter(requer_treinamento=True).count(),
        "total_grupo_whatsapp": queryset.filter(grupo_whatsapp=True).count(),
        "total_sem_pdf": queryset.filter(Q(pdf_integracao__isnull=True) | Q(pdf_integracao="")).count(),
    }
