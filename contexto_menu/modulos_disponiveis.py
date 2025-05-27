def listar_modulos(user):
    modulos = []

    if user.has_perm("Funcionario.acesso_rh"):
        modulos.append({
            "name": "Recursos Humanos",
            "url": "home",
            "icon": "bi bi-people",
            "permissao": "Funcionario.acesso_rh",
        })

    if user.has_perm("metrologia.acesso_metrologia"):
        modulos.append({
            "name": "Metrologia",
            "url": "metrologia_home",
            "icon": "bi bi-rulers",
            "permissao": "metrologia.acesso_metrologia",
        })

    if user.has_perm("qualidade_fornecimento.acesso_qualidade"):
        modulos.append({
            "name": "Qualidade de Fornecimento",
            "url": "qualidadefornecimento_home",
            "icon": "fas fa-industry",
            "permissao": "qualidade_fornecimento.acesso_qualidade",
        })

    if user.has_perm("portaria.acesso_portaria"):
        modulos.append({
            "name": "Portaria",
            "url": "portaria_home",
            "icon": "fas fa-door-open",
            "permissao": "portaria.acesso_portaria",
        })

    return modulos
