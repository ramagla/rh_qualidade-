from django.contrib import admin

from .models import Alerta, AlertaConfigurado, AlertaUsuario


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "descricao")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")

@admin.register(AlertaConfigurado)
class AlertaConfiguradoAdmin(admin.ModelAdmin):
    list_display    = ("tipo", "ativo")
    list_filter     = ("ativo",)
    search_fields   = ("tipo",)
    filter_horizontal = ("usuarios", "grupos")

@admin.register(AlertaUsuario)
class AlertaUsuarioAdmin(admin.ModelAdmin):
    list_display   = ("titulo", "usuario", "tipo", "criado_em", "lido")
    list_filter    = ("tipo", "lido", "excluido")
    search_fields  = ("titulo", "mensagem", "usuario__username")
    readonly_fields = ("criado_em",)
    date_hierarchy = "criado_em"