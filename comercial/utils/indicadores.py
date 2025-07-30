from comercial.models.indicadores import IndicadorComercialRegistroMensal

def salvar_registro_indicador(indicador, ano, mes=None, trimestre=None, valor=0.0, media=0.0, meta=0.0,
                               total_realizados=0, total_aprovados=0, comentario=""):
    if not mes and not trimestre:
        raise ValueError("É necessário informar 'mes' ou 'trimestre'.")

    obj, created = IndicadorComercialRegistroMensal.objects.get_or_create(
        indicador=indicador,
        ano=ano,
        mes=mes,
        trimestre=trimestre,
        defaults={
            "valor": valor,
            "media": media,
            "meta": meta,
            "total_realizados": total_realizados,
            "total_aprovados": total_aprovados,
            "comentario": comentario
        }
    )
    return obj, created
