# contexto_menu/home.py

def menu_home(user):
    menu = []

    if user.has_perm("Funcionario.view_documento"):
        menu.append({
            "name": "Documentos",
            "url": "lista_documentos",
            "icon": "bi bi-file-earmark-text",
        })

    # Adicione mais itens no futuro se a Home tiver outros recursos

    return menu
