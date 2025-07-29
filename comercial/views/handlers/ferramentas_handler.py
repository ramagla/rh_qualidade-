from django.utils import timezone
from django.forms import inlineformset_factory
from comercial.forms.precalculos_form import CotacaoFerramentaForm
from comercial.models.precalculo import PreCalculo, CotacaoFerramenta
from comercial.utils.assinatura_utils import criar_assinatura_eletronica  # ✅ IMPORT PADRÃO

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
            instancias = fs_ferr.save(commit=False)
            for inst in instancias:
                inst.usuario = request.user
                inst.assinatura_nome = request.user.get_full_name()
                inst.assinatura_cn = request.user.email
                inst.data_assinatura = timezone.now()
                inst.assinado_em = timezone.now()
                inst.save()

                criar_assinatura_eletronica(inst)  # ✅ MESMA ASSINATURA PADRÃO

            fs_ferr.save_m2m()
            print("✅ Ferramentas salvas com sucesso e metadados preenchidos")
            return True, fs_ferr
        else:
            print("❌ Formulário de ferramentas inválido:", fs_ferr.errors)

    return False, fs_ferr
