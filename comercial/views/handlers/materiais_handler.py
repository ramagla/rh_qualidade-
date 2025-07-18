from django.forms import inlineformset_factory
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoMaterialForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.utils.precalculo_utils import atualizar_materiais_do_roteiro  # ⬅️ Certifique-se que essa função está acessível aqui


def processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo=None):
    salvo = False

    # 🔄 Atualização manual: botão "Atualizar do Roteiro"
    if request.method == "POST" and request.POST.get("atualizar_materiais") == "1":
        atualizar_materiais_do_roteiro(precalc)

    # Primeira carga via GET se não houver materiais
    if request.method == "GET" and not precalc.materiais.exists():
        atualizar_materiais_do_roteiro(precalc)

    qs_materiais = PreCalculoMaterial.objects.filter(precalculo=precalc)

    MatSet = inlineformset_factory(
        PreCalculo,
        PreCalculoMaterial,
        form=PreCalculoMaterialForm,
        extra=0,
        can_delete=True,
    )

    fs_mat = MatSet(instance=precalc, queryset=qs_materiais, prefix="mat")

    if request.method == "POST" and not request.POST.get("atualizar_materiais"):
        data = request.POST.copy()
        total = int(data.get("mat-TOTAL_FORMS", 0))

        for i in range(total):
            campo = f"mat-{i}-peso_bruto_total"
            valor = data.get(campo)
            if valor:
                try:
                    valor = valor.replace(".", "").replace(",", ".")
                    data[campo] = str(Decimal(valor))
                except Exception as e:
                    data[campo] = ""

        assert form_precalculo is not None, "form_precalculo não foi passado corretamente"

        fs_mat = MatSet(data=data, instance=precalc, queryset=qs_materiais, prefix="mat")

        if "form_materiais_submitted" in request.POST:
            if fs_mat.is_valid():
                selecionado = request.POST.get("material_selecionado")
                codigos_disparados = set()

                for mat_form in fs_mat:
                    if mat_form.cleaned_data and not mat_form.cleaned_data.get("DELETE", False):
                        mat = mat_form.save(commit=False)

                        if not mat.descricao:
                            mat.descricao = mat_form.cleaned_data.get("descricao") or mat.nome_materia_prima or ""
                        if not mat.tipo_material:
                            mat.tipo_material = mat_form.cleaned_data.get("tipo_material") or mat.tipo_material or ""

                        mat.selecionado = (mat_form.prefix == selecionado)

                        qtde_estimada = getattr(precalc.analise_comercial_item, "qtde_estimada", 0)
                        if mat.peso_bruto and qtde_estimada:
                            mat.peso_bruto_total = Decimal(mat.peso_bruto) * Decimal(qtde_estimada)

                        try:
                            mp = MateriaPrimaCatalogo.objects.get(codigo=mat.codigo)
                            if not mat.descricao:
                                mat.descricao = mp.descricao
                            if not mat.tipo_material:
                                mat.tipo_material = mp.tipo_material
                        except MateriaPrimaCatalogo.DoesNotExist:
                            pass

                        mat.save()

                        if (
                            not materiais_respondidos and
                            mat.codigo and not mat.preco_kg and
                            mat.codigo not in codigos_disparados
                        ):
                            disparar_email_cotacao_material(request, mat)
                            codigos_disparados.add(mat.codigo)

                fs_mat.save()
                salvo = True
            else:
                print("❌ Erros no formset de materiais:")
                for form in fs_mat:
                    print(form.errors)
                print("non_form_errors:", fs_mat.non_form_errors())

    return salvo, form_precalculo, fs_mat
