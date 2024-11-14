from django.contrib import admin
from .models import Treinamento, AvaliacaoTreinamento,AtualizacaoSistema,Settings

admin.site.register(Treinamento)
admin.site.register(AvaliacaoTreinamento)

@admin.register(AtualizacaoSistema)
class AtualizacaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'descricao', 'previsao', 'versao')  # Mostra o campo versão no admin
    search_fields = ('titulo',)
    list_filter = ('previsao',)
    ordering = ('-previsao',)  # Exibe as atualizações mais recentes no topo


admin.site.register(Settings)
