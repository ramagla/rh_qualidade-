# comercial/utils/ferramentas_handler.py
from django.utils import timezone
from django.forms import inlineformset_factory
from comercial.forms.precalculos_form import CotacaoFerramentaForm
from comercial.models.precalculo import PreCalculo, CotacaoFerramenta
from comercial.utils.assinatura_utils import criar_assinatura_eletronica

def processar_aba_ferramentas(request, precalc):
    # ✅ Permite múltiplas ferramentas: remove max_num e deixa can_delete
    FerrSet = inlineformset_factory(
        PreCalculo,
        CotacaoFerramenta,
        form=CotacaoFerramentaForm,
        extra=1,              # uma linha vazia pronta; usuário pode adicionar mais no template
        can_delete=True       # habilita exclusão por linha
    )

    fs_ferr = FerrSet(
        request.POST if request.method == "POST" else None,
        instance=precalc,
        prefix="ferr"
    )

    if request.method == "POST" and request.POST.get("form_ferramentas_submitted"):
        if fs_ferr.is_valid():
            # Salva novas/alteradas (commit=False para preencher metadados)
            objetos = fs_ferr.save(commit=False)
            for obj in objetos:
                obj.usuario = request.user
                obj.assinatura_nome = request.user.get_full_name()
                obj.assinatura_cn = request.user.email
                obj.data_assinatura = timezone.now()
                obj.assinado_em = timezone.now()
                obj.save()
                criar_assinatura_eletronica(obj)

            # Remove itens marcados para exclusão
            for obj in fs_ferr.deleted_objects:
                obj.delete()

            fs_ferr.save_m2m()
            print("✅ Ferramentas salvas/excluídas com sucesso.")
            return True, fs_ferr
        else:
            print("❌ Formulário de ferramentas inválido:", fs_ferr.errors)

    return False, fs_ferr
