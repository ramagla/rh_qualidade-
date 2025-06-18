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

    if user.has_perm("comercial.acesso_comercial"):
        modulos.append({
            "name": "Comercial",
            "url": "comercial_home",
            "icon": "fas fa-chart-line",
            "permissao": "comercial.acesso_comercial",
        })

    if user.has_perm("tecnico.acesso_tecnico"):
        modulos.append({
            "name": "Técnico",
            "url": "tecnico:tecnico_home",
            "icon": "bi bi-tools",
            "permissao": "tecnico.acesso_tecnico",
        })




    return modulos
