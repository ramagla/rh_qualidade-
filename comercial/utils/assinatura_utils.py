from assinatura_eletronica.utils import gerar_assinatura

def criar_assinatura_eletronica(obj):
    from assinatura_eletronica.models import AssinaturaEletronica

    usuario = getattr(obj, "usuario", None)
    if not usuario:
        return

    # Tenta encontrar um campo de conclusão válido
    conclusao = ""
    for campo in ["conclusao", "conclusao_comercial", "conclusao_tec", "conclusao_desenvolvimento"]:
        if hasattr(obj, campo):
            conclusao = getattr(obj, campo)
            break

    hash_valido = gerar_assinatura(obj, usuario)
    conteudo = f"{obj.__class__.__name__.upper()}|{obj.pk}|{conclusao}"

    AssinaturaEletronica.objects.get_or_create(
        hash=hash_valido,
        defaults={
            "conteudo": conteudo,
            "usuario": usuario,
            "origem_model": obj.__class__.__name__,
            "origem_id": obj.pk,
        }
    )
