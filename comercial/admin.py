from django.contrib import admin
from .models.indicadores import IndicadorComercialRegistroMensal

@admin.register(IndicadorComercialRegistroMensal)
class IndicadorComercialRegistroAdmin(admin.ModelAdmin):
    list_display = ("indicador", "ano", "mes", "trimestre", "valor", "meta", "media", "criado_em")
    list_filter = ("indicador", "ano", "mes", "trimestre")
    search_fields = ("comentario",)



from django.contrib import admin
from comercial.models.faturamento import FaturamentoRegistro

@admin.register(FaturamentoRegistro)
class FaturamentoRegistroAdmin(admin.ModelAdmin):
    list_display = ("nfe","cliente","ocorrencia","item_codigo","item_quantidade","item_valor_unitario","valor_frete","congelado","atualizado_em")
    list_filter = ("congelado","ocorrencia")
    search_fields = ("nfe","cliente","item_codigo")
    actions = ["marcar_congelado","desmarcar_congelado"]

    @admin.action(description="Marcar como congelado")
    def marcar_congelado(self, request, queryset):
        queryset.update(congelado=True)

    @admin.action(description="Desmarcar congelado")
    def desmarcar_congelado(self, request, queryset):
        queryset.update(congelado=False)


from django.contrib import admin
from comercial.models.indicadores import MetaFaturamento

@admin.register(MetaFaturamento)
class MetaFaturamentoAdmin(admin.ModelAdmin):
    list_display = ("ano", "mes", "valor")
    list_filter = ("ano", "mes")
    search_fields = ("ano",)
    ordering = ("-ano", "mes")
