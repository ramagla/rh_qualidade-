# metrologia/context_processors.py
from django.shortcuts import render

def global_metrologia_settings(request):
    # Atualizando menu_items no context_processors.py
    menu_items = [
        {'name': 'Instrumentos', 'url': 'metrologia_home', 'icon': 'fas fa-ruler-combined'},
        {'name': 'Calibrações', 'url': 'metrologia_calibracoes', 'icon': 'fas fa-cogs'},
        {'name': 'Relatórios', 'url': 'metrologia_relatorios', 'icon': 'fas fa-file-alt'},
        {'name': 'Configurações', 'url': 'metrologia_configuracoes', 'icon': 'fas fa-cog'},
    ]


    return {
        'nome_modulo': 'Metrologia',
        'icone_modulo': 'bi-rulers',
        'menu_items': menu_items,
    }
