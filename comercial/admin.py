from django.contrib import admin
from .models.indicadores import IndicadorComercialRegistroMensal

@admin.register(IndicadorComercialRegistroMensal)
class IndicadorComercialRegistroAdmin(admin.ModelAdmin):
    list_display = ("indicador", "ano", "mes", "trimestre", "valor", "meta", "media", "criado_em")
    list_filter = ("indicador", "ano", "mes", "trimestre")
    search_fields = ("comentario",)
