def menu_home(user):
    menu = []

    if user.has_perm("Funcionario.view_documento"):
        menu.append({
            "name": "Documentos",
            "url": "lista_documentos",
            "icon": "bi bi-file-earmark-text",
        })

    if user.has_perm("Funcionario.view_recibopagamento"):
        menu.append({
            "name": "Recibos de Pagamento",
            "url": "recibos_pagamento",
            "icon": "bi bi-receipt",
        })


    return menu
