from django.forms import inlineformset_factory
from comercial.forms.precalculos_form import CotacaoFerramentaForm
from comercial.models.precalculo import PreCalculo, CotacaoFerramenta

def processar_aba_ferramentas(request, precalc):
    FerrSet = inlineformset_factory(
        PreCalculo,
        CotacaoFerramenta,
        form=CotacaoFerramentaForm,
        extra=1,
        max_num=1,
        can_delete=True
    )

    fs_ferr = FerrSet(
        request.POST if request.method == "POST" else None,
        instance=precalc,
        prefix="ferr"
    )

    if request.method == "POST" and request.POST.get("form_ferramentas_submitted"):
        if fs_ferr.is_valid():
            # 🟢 Salva diretamente, sem checar se houve alteração
            fs_ferr.save()
            print("✅ Ferramentas salvas com sucesso (sem validação de alterações)")
            return True, fs_ferr
        else:
            print("❌ Formset de ferramentas inválido:", fs_ferr.errors)

    return False, fs_ferr
