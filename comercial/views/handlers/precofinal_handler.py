from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from comercial.forms.precalculos_form import PrecoFinalForm
from django.utils.html import strip_tags


def processar_aba_precofinal(request, precalc):
    print("🔵 INICIANDO processamento da aba Preço Final")

    form = PrecoFinalForm(None, instance=precalc)

    if request.method == "POST":
        print("📥 POST detectado com submissão da aba Preço Final")
        print("📦 request.POST =", request.POST)

        preco_raw = request.POST.get("preco_selecionado", "").strip().replace(",", ".")
        preco_manual_raw = request.POST.get("preco_manual", "").strip().replace(",", ".")

        mutable_post = request.POST.copy()
        mutable_post["preco_manual"] = preco_manual_raw

        try:
            preco_tabela = Decimal(preco_raw) if preco_raw else None
        except InvalidOperation:
            print("❌ Erro ao converter preco_selecionado")
            preco_tabela = None

        try:
            preco_manual_unit = Decimal(preco_manual_raw) if preco_manual_raw else None
            if preco_manual_unit is not None:
                preco_manual_unit = preco_manual_unit.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            print("❌ Erro ao converter preco_manual")
            preco_manual_unit = None

        form = PrecoFinalForm(mutable_post, instance=precalc)

        if form.is_valid():
            preco_atual = precalc.preco_selecionado or Decimal("0.00")
            manual_atual = precalc.preco_manual or Decimal("0.00")

            print(f"💡 preco_manual_unit = {preco_manual_unit}")
            print(f"💡 preco_tabela = {preco_tabela}")
            print(f"💡 preco_atual = {preco_atual}")
            print(f"💡 manual_atual = {manual_atual}")

            campos_alterados = []

            # Preço final (manual ou da tabela)
            if preco_manual_unit is not None and preco_manual_unit > 0:
                if preco_manual_unit != manual_atual:
                    precalc.preco_manual = preco_manual_unit
                    precalc.preco_selecionado = preco_manual_unit
                    campos_alterados += ["preco_manual", "preco_selecionado"]

            elif preco_tabela is not None:
                preco_tabela = preco_tabela.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                if preco_tabela != preco_atual:
                    precalc.preco_selecionado = preco_tabela
                    precalc.preco_manual = Decimal("0.00")
                    campos_alterados += ["preco_selecionado", "preco_manual"]

            # Observações – comparação com texto limpo (sem tags)
            precalc.observacoes_precofinal = form.cleaned_data["observacoes_precofinal"]
            campos_alterados.append("observacoes_precofinal")




            if campos_alterados:
                precalc.save(update_fields=campos_alterados)
                print("💾 Campos salvos com sucesso:", campos_alterados)

                return (
                    True, form,
                    precalc.calcular_precos_sem_impostos(),
                    precalc.calcular_precos_com_impostos(),
                    "Preço salvo com sucesso."
                )
            else:
                print("⚠️ Nenhuma alteração detectada")
                return (
                    False, form,
                    precalc.calcular_precos_sem_impostos(),
                    precalc.calcular_precos_com_impostos(),
                    "Nenhuma alteração detectada."
                )
        else:
            print("❌ Formulário inválido. Erros:", form.errors)
            return (
                False, form,
                precalc.calcular_precos_sem_impostos(),
                precalc.calcular_precos_com_impostos(),
                "Erro no formulário."
            )

    print("🔵 GET ou POST sem alteração válida.")
    return (
        False, form,
        precalc.calcular_precos_sem_impostos(),
        precalc.calcular_precos_com_impostos(),
        "GET ou POST sem alteração válida."
    )
