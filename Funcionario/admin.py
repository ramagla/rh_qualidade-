from django.contrib import admin
from .models import Treinamento, AvaliacaoTreinamento,AtualizacaoSistema

admin.site.register(Treinamento)
admin.site.register(AvaliacaoTreinamento)

@admin.register(AtualizacaoSistema)
class AtualizacaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'previsao')
    search_fields = ('titulo',)
    list_filter = ('previsao',)
    ordering = ('-previsao',)  # Exibe as atualizações mais recentes no topo