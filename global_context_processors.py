from datetime import datetime
from Funcionario.models import AtualizacaoSistema

def global_menu(request):
    user = request.user

    # Verificar permissões do usuário para os módulos
    metrologia_permitido = user.has_perm("metrologia.acesso_metrologia")
    recursos_humanos_permitido = user.has_perm("Funcionario.acesso_rh")
    qualidade_fornecimento_permitido = user.has_perm("qualidade_fornecimento.acesso_qualidade")
    portaria_permitido = user.has_perm("portaria.acesso_portaria")  # ✅ NOVO


    # Menu Metrologia
    menu_metrologia = []
    if metrologia_permitido:
        menu_metrologia.append({
            "name": "Dashboard",
            "url": "metrologia_home",
            "icon": "fas fa-tachometer-alt",
        })
        if user.has_perm("metrologia.view_tabelatecnica"):
            menu_metrologia.append({
                "name": "Cadastros",
                "icon": "fas fa-folder",
                "submenu": [
                    {"name": "Instrumentos", "url": "lista_tabelatecnica", "icon": "fas fa-ruler-combined", "perm": "metrologia.view_tabelatecnica"},
                    {"name": "Dispositivos", "url": "lista_dispositivos", "icon": "fas fa-cogs"},
                ],
            })
        if user.has_perm("metrologia.view_calibracaodispositivo") or user.has_perm("metrologia.view_calibracao"):
            menu_metrologia.append({
                "name": "Calibrações",
                "icon": "fas fa-cogs",
                "submenu": [
                    {"name": "Calibrações de Instrumentos", "url": "calibracoes_instrumentos", "icon": "fas fa-tools"},
                    {"name": "Calibrações de Dispositivos", "url": "lista_calibracoes_dispositivos", "icon": "fas fa-wrench"},
                ],
            })
        if user.has_perm("metrologia.view_cronograma"):
            menu_metrologia.append({
                "name": "Cronogramas",
                "icon": "fas fa-calendar-alt",
                "submenu": [
                    {"name": "Cronograma de Equipamentos", "url": "cronograma_calibracao"},
                    {"name": "Cronograma de Dispositivos", "url": "cronograma_dispositivos"},
                ],
            })
        if user.has_perm("metrologia.view_relatorio"):
            menu_metrologia.append({
                "name": "Relatórios",
                "icon": "fas fa-file-alt",
                "submenu": [
                    {"name": "Equipamentos a Calibrar", "url": "relatorio_equipamentos_calibrar", "icon": "fas fa-exclamation-circle"},
                    {"name": "Equipamentos por Funcionário", "url": "equipamentos_por_funcionario", "icon": "fas fa-users"},
                ],
            })
        if user.has_perm("Funcionario.view_documento"):
            menu_metrologia.append({
                "name": "Documentos",
                "url": "lista_documentos",
                "icon": "fas fa-folder-open",
            })

   # Menu Recursos Humanos
    menu_recursos_humanos = []
    if recursos_humanos_permitido:

        # Dashboard (ainda pode depender de view_funcionario)
        if user.has_perm("Funcionario.view_funcionario"):
            menu_recursos_humanos.append({
                "name": "Dashboard",
                "url": "funcionarios_home",
                "icon": "fas fa-tachometer-alt",
            })

        # Colaboradores (individual)
        if user.has_perm("Funcionario.view_funcionario"):
            menu_recursos_humanos.append({
                "name": "Colaboradores",
                "url": "lista_funcionarios",
                "icon": "fas fa-user",
            })

        # Integrações (individual)
        if user.has_perm("Funcionario.view_integracaofuncionario"):
            menu_recursos_humanos.append({
                "name": "Integrações",
                "url": "lista_integracoes",
                "icon": "bi bi-person-badge",
            })

        # Comunicados Internos (independente)
        if user.has_perm("Funcionario.view_comunicado"):
            menu_recursos_humanos.append({
                "name": "Comunicados Internos",
                "url": "lista_comunicados",
                "icon": "fas fa-bullhorn",
            })

        # Cargos
        if user.has_perm("Funcionario.view_cargo") or user.has_perm("Funcionario.add_cargo"):
            menu_recursos_humanos.append({
                "name": "Cargos",
                "url": "lista_cargos",
                "icon": "fas fa-briefcase",
            })

        # Treinamentos
        if (
            user.has_perm("Funcionario.view_treinamento") or
            user.has_perm("Funcionario.view_listapresenca") or
            user.has_perm("Funcionario.view_avaliacaotreinamento")
        ):
            submenu_treinamentos = []

            if user.has_perm("Funcionario.view_treinamento"):
                submenu_treinamentos.append({
                    "name": "Lista de Treinamentos",
                    "url": "lista_treinamentos"
                })

            if user.has_perm("Funcionario.view_listapresenca"):
                submenu_treinamentos.append({
                    "name": "Lista de Presença",
                    "url": "lista_presenca"
                })

            if user.has_perm("Funcionario.view_avaliacaotreinamento"):
                submenu_treinamentos.append({
                    "name": "Avaliação de Treinamentos",
                    "url": "lista_avaliacoes"
                })

            if submenu_treinamentos:
                menu_recursos_humanos.append({
                    "name": "Treinamentos",
                    "icon": "fas fa-graduation-cap",
                    "submenu": submenu_treinamentos,
                })

        # Desempenho
        if user.has_perm("Funcionario.view_avaliacaoanual") or user.has_perm("Funcionario.view_avaliacaoexperiencia"):
            menu_recursos_humanos.append({
                "name": "Desempenho",
                "icon": "fas fa-chart-line",
                "submenu": [
                    {"name": "Anual", "url": "lista_avaliacao_anual"},
                    {"name": "Experiência", "url": "lista_avaliacao_experiencia"},
                ],
            })

        # Job Rotation
        if user.has_perm("Funcionario.view_jobrotationevaluation"):
            menu_recursos_humanos.append({
                "name": "Job Rotation",
                "url": "lista_jobrotation_evaluation",
                "icon": "fas fa-sync-alt",
            })

        # Matriz de Polivalência
        if user.has_perm("Funcionario.view_matrizpolivalencia"):
            menu_recursos_humanos.append({
                "name": "Matriz de Polivalência",
                "icon": "fas fa-layer-group",
                "submenu": [
                    {"name": "Lista de Atividades", "url": "lista_atividades"},
                    {"name": "Lista de Matriz", "url": "lista_matriz_polivalencia"},
                ],
            })

        # Relatórios
        submenu_relatorios = []

        if user.has_perm("Funcionario.relatorio_indicador"):
            submenu_relatorios.append({
                "name": "Indicador de Treinamentos",
                "url": "relatorio_indicador"
            })

        if user.has_perm("Funcionario.cronograma_treinamentos"):
            submenu_relatorios.append({
                "name": "Cronograma de Treinamentos",
                "url": "cronograma_treinamentos"
            })

        if user.has_perm("Funcionario.cronograma_avaliacao_eficacia"):
            submenu_relatorios.append({
                "name": "Acompanhamento de Eficácia",
                "url": "cronograma_avaliacao_eficacia"
            })

        if user.has_perm("Funcionario.relatorio_indicador_anual"):
            submenu_relatorios.append({
                "name": "Indicador Anual",
                "url": "relatorio_indicador_anual"
            })

        if user.has_perm("Funcionario.relatorio_aniversariantes"):
            submenu_relatorios.append({
                "name": "Aniversariantes do Mês",
                "url": "relatorio_aniversariantes"
            })

        if submenu_relatorios:
            menu_recursos_humanos.append({
                "name": "Relatórios",
                "icon": "fas fa-file-alt",
                "submenu": submenu_relatorios,
            })


        # Formulários (novas permissões customizadas)
        submenu_formularios = []

        if user.has_perm("Funcionario.emitir_carta_competencia"):
            submenu_formularios.append({
                "name": "Carta de Competência",
                "url": "filtro_funcionario"
            })

        if user.has_perm("Funcionario.emitir_pesquisa_consciencia"):
            submenu_formularios.append({
                "name": "Pesquisa de Consciência",
                "url": "formulario_pesquisa_consciencia"
            })

        if user.has_perm("Funcionario.emitir_capacitacao_pratica"):
            submenu_formularios.append({
                "name": "Avaliação de Capacitação Prática",
                "url": "filtro_carta_competencia"
            })

        if user.has_perm("Funcionario.emitir_f033"):
            submenu_formularios.append({
                "name": "Solicitação de Bolsa-Treinamento (F033)",
                "url": "filtro_funcionario_f033"
            })



        if submenu_formularios:
            menu_recursos_humanos.append({
                "name": "Formulários",
                "icon": "fas fa-edit",
                "submenu": submenu_formularios,
            })
       

        # Documentos
        if user.has_perm("Funcionario.view_documento"):
            menu_recursos_humanos.append({
                "name": "Documentos",
                "url": "lista_documentos",
                "icon": "fas fa-folder-open",
            })

        # Calendário
        if user.has_perm("Funcionario.view_calendario"):
            menu_recursos_humanos.append({
                "name": "Calendário",
                "url": "calendario",
                "icon": "fas fa-calendar-alt",
            })



    # Módulos disponíveis
    modulos_disponiveis = []
    if recursos_humanos_permitido:
        modulos_disponiveis.append({
            "name": "Recursos Humanos",
            "url": "home",
            "icon": "bi bi-people",
            "permissao": "Funcionario.acesso_rh",
        })
    if metrologia_permitido:
        modulos_disponiveis.append({
            "name": "Metrologia",
            "url": "metrologia_home",
            "icon": "bi bi-rulers",
            "permissao": "metrologia.acesso_metrologia",
        })
    if qualidade_fornecimento_permitido:
        modulos_disponiveis.append({
            "name": "Qualidade de Fornecimento",
            "url": "qualidadefornecimento_home",
            "icon": "fas fa-industry",
            "permissao": "qualidade_fornecimento.acesso_qualidade",
        })
    if portaria_permitido:
        modulos_disponiveis.append({
            "name": "Portaria",
            "url": "lista_pessoas",
            "icon": "fas fa-door-open",
            "permissao": "portaria.acesso_portaria",
        })

    # Menu Qualidade de Fornecimento
    menu_qualidade_fornecimento = []
    if qualidade_fornecimento_permitido:
        if user.has_perm("qualidade_fornecimento.dashboard_qualidade"):
            menu_qualidade_fornecimento.append({
                "name": "Dashboard",
                "url": "qualidadefornecimento_home",
                "icon": "fas fa-industry",
            })

        # Cadastros
        submenu_cadastros = []

        if user.has_perm("qualidade_fornecimento.view_fornecedorqualificado"):
            submenu_cadastros.append({
                "name": "Fornecedores",
                "url": "lista_fornecedores",
                "icon": "fas fa-truck",
            })

        if user.has_perm("qualidade_fornecimento.view_normatecnica"):
            submenu_cadastros.append({
                "name": "Normas Técnicas",
                "url": "lista_normas",
                "icon": "fas fa-file-alt",
            })

        if user.has_perm("qualidade_fornecimento.view_materiaprimacatalogo"):
            submenu_cadastros.append({
                "name": "Catálogo de Matéria-Prima",
                "url": "materiaprima_catalogo_list",
                "icon": "fas fa-tags",
            })

        if submenu_cadastros:
            menu_qualidade_fornecimento.append({
                "name": "Cadastros",
                "icon": "fas fa-folder-open",
                "submenu": submenu_cadastros,
            })

        if user.has_perm("qualidade_fornecimento.view_relacaomateriaprima"):
            menu_qualidade_fornecimento.append({
                "name": "TB050 - Relação de Matérias-Primas",
                "url": "tb050_list",
                "icon": "fas fa-boxes",
            })

        if user.has_perm("qualidade_fornecimento.view_controleservicoexterno"):
            menu_qualidade_fornecimento.append({
                "name": "Controle de Serviço Externo",
                "url": "listar_controle_servico_externo",
                "icon": "fas fa-external-link-alt",
            })

        if user.has_perm("qualidade_fornecimento.view_fornecedorqualificado"):
            menu_qualidade_fornecimento.append({
                "name": "Relatórios",
                "icon": "fas fa-file-alt",
                "submenu": [
                    {
                        "name": "Avaliação Semestral",
                        "url": "relatorio_avaliacao",
                        "icon": "fas fa-chart-line",
                    },
                ],
            })

       
      # Menu Cadastros (agrupando submenus da portaria)
        menu_cadastros = []

        if portaria_permitido:
            submenu_portaria = []

            submenu_portaria.append({
                "name": "Pessoas",
                "url": "lista_pessoas",
                "icon": "fas fa-door-open",
            })

            if user.has_perm("portaria.view_veiculoportaria"):
                submenu_portaria.append({
                    "name": "Veículos",
                    "url": "lista_veiculos",
                    "icon": "fas fa-car-side",
                })

            menu_cadastros.append({
                "name": "Cadastros",
                "icon": "fas fa-folder-open",
                "submenu": submenu_portaria
            })

        # Menu simples: Controle de Visitantes
            if user.has_perm("portaria.view_controlevisitantes"):
                menu_cadastros.append({
                    "name": "Controle de Visitantes",
                    "url": "listar_controle_visitantes",
                    "icon": "fas fa-user-check"
                })

        # Menu simples: Controle de Atrasos e Saídas Antecipadas
            if user.has_perm("portaria.view_funcionario"):  # ou crie uma permissão específica se desejar
                menu_cadastros.append({
                    "name": "Atrasos e Saídas Antecipadas",
                    "url": "lista_atrasos_saidas",
                    "icon": "fas fa-user-clock"
                })

                    # Menu simples: Controle de Ligações
            if user.has_perm("portaria.view_ligacaoportaria"):
                menu_cadastros.append({
                    "name": "Controle de Ligações",
                    "url": "lista_ligacoes",
                    "icon": "fas fa-phone-alt"
                })
            if user.has_perm("portaria.view_ocorrenciaportaria"):
                menu_cadastros.append({
                    "name": "Ocorrências da Portaria",
                    "url": "listar_ocorrencias",
                    "icon": "fas fa-exclamation-triangle"
                })


           

    active_module = request.path.split("/")[1]
    if active_module == "metrologia":
        menu = menu_metrologia
        modulo_ativo = next((m for m in modulos_disponiveis if m["name"] == "Metrologia"), None)
    elif active_module == "qualidade":
        menu = menu_qualidade_fornecimento
        modulo_ativo = next((m for m in modulos_disponiveis if m["name"] == "Qualidade de Fornecimento"), None)
    elif active_module == "portaria":
        menu = menu_cadastros  # ✅ agora é este o nome correto
        modulo_ativo = next((m for m in modulos_disponiveis if m["name"] == "Portaria"), None)

    else:
        menu = menu_recursos_humanos
        modulo_ativo = next((m for m in modulos_disponiveis if m["name"] == "Recursos Humanos"), None)


    from alerts.models import AlertaUsuario
    if user.is_authenticated:
        alertas_nao_lidos = AlertaUsuario.objects.filter(usuario=user, lido=False).count()
        ultimos_alertas = AlertaUsuario.objects.filter(usuario=user).order_by("-criado_em")[:5]
    else:
        alertas_nao_lidos = 0
        ultimos_alertas = []

    ultima = AtualizacaoSistema.objects.filter(status="concluido").order_by("-data_termino").first()
    historico = AtualizacaoSistema.objects.filter(status="concluido").exclude(id=ultima.id if ultima else None).order_by("-data_termino")

    return {
        "menu": menu,
        "modulo_ativo": modulo_ativo,
        "modulos_disponiveis": modulos_disponiveis,
        "ano_atual": datetime.now().year,
        "alertas_nao_lidos": alertas_nao_lidos,
        "ultimos_alertas": ultimos_alertas,
        "ultima_atualizacao_concluida": ultima,
        "historico_versoes": historico,
    }
