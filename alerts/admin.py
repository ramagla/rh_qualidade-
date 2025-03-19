from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "descricao")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")
