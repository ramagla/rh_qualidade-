from django import forms
from django.contrib import admin
from django_ckeditor_5.widgets import CKEditor5Widget

from Funcionario.models import (
    AtualizacaoSistema,
    AvaliacaoTreinamento,
    Settings,
    Treinamento,
)

# Registro dos modelos simples
admin.site.register(Treinamento)
admin.site.register(AvaliacaoTreinamento)
admin.site.register(Settings)

# Formulário personalizado para usar CKEditor no campo 'descricao'


class AtualizacaoSistemaForm(forms.ModelForm):
    class Meta:
        model = AtualizacaoSistema
        fields = "__all__"
        widgets = {
            "descricao": CKEditor5Widget(),  # Aplica CKEditor ao campo 'descricao'
        }


# Configuração do admin para AtualizacaoSistema


@admin.register(AtualizacaoSistema)
class AtualizacaoSistemaAdmin(admin.ModelAdmin):
    form = AtualizacaoSistemaForm
    list_display = ("titulo", "previsao", "versao", "status")
    search_fields = ("titulo",)
    list_filter = ("previsao",)
    ordering = ("-previsao",)  # Ordena por previsão mais recente primeiro


from django.contrib import admin
from .models.departamentos import Departamentos

@admin.register(Departamentos)
class DepartamentosAdmin(admin.ModelAdmin):
    list_display = ["nome", "sigla", "ativo"]
    search_fields = ["nome", "sigla"]
    list_filter = ["ativo"]

