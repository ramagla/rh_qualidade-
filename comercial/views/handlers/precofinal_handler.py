from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from comercial.forms.precalculos_form import PrecoFinalForm


def processar_aba_precofinal(request, precalc):
    print("🔵 INICIANDO processamento da aba Preço Final")

    form = PrecoFinalForm(None, instance=precalc)

    if request.method == "POST":
        print("📥 POST detectado com submissão da aba Preço Final")
        print("📦 request.POST =", request.POST)

        # 🔁 DE: campos brutos diretamente do POST (com vírgula)
        preco_raw = request.POST.get("preco_selecionado", "").strip().replace(",", ".")
        preco_manual_raw = request.POST.get("preco_manual", "").strip().replace(",", ".")

        # ✅ PARA: sobrescreve o POST antes da validação do form
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

        # ⬅️ DE: form = PrecoFinalForm(request.POST, instance=precalc)
        # ✅ PARA: usa o POST mutável com "." no lugar da vírgula
        form = PrecoFinalForm(mutable_post, instance=precalc)

        if form.is_valid():
            preco_atual = precalc.preco_selecionado or Decimal("0.00")
            manual_atual = precalc.preco_manual or Decimal("0.00")

            print(f"💡 preco_manual_unit = {preco_manual_unit}")
            print(f"💡 preco_tabela = {preco_tabela}")
            print(f"💡 preco_atual = {preco_atual}")
            print(f"💡 manual_atual = {manual_atual}")

            preco_salvo = None

            if preco_manual_unit is not None and preco_manual_unit > 0:
                preco_salvo = preco_manual_unit
                print(f"✅ Usando preco_manual (unitário) = {preco_salvo}")
                precalc.preco_manual = preco_salvo
                precalc.preco_selecionado = Decimal("0.00")

            elif preco_tabela is not None:
                preco_salvo = preco_tabela.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                print(f"✅ Usando preco_tabela (unitário) = {preco_salvo}")
                precalc.preco_selecionado = preco_salvo
                precalc.preco_manual = Decimal("0.00")

            if preco_salvo is not None:
                precalc.save(update_fields=["preco_selecionado", "preco_manual"])
                print("💾 Preço salvo com sucesso:", preco_salvo)

                return (
                    True, form,
                    precalc.calcular_precos_sem_impostos(),
                    precalc.calcular_precos_com_impostos(),
                    "Preço salvo com sucesso."
                )
            else:
                print("⚠️ Nenhum valor válido informado")
                return (
                    False, form,
                    precalc.calcular_precos_sem_impostos(),
                    precalc.calcular_precos_com_impostos(),
                    "Nenhum valor válido informado."
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
