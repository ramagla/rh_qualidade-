from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from .models import Funcionario, HistoricoCargo, JobRotationEvaluation, Treinamento


@receiver(m2m_changed, sender=Treinamento.funcionarios.through)
def atualizar_escolaridade_funcionario(
    sender, instance, action, reverse, pk_set, **kwargs
):
    """
    Atualiza a escolaridade dos funcionários associados ao treinamento quando
    há alterações na relação Many-to-Many.
    """
    if (
        action == "post_add"
        and instance.status == "concluido"
        and instance.categoria
        in ["tecnico", "graduacao", "pos-graduacao", "mestrado", "doutorado"]
    ):
        for funcionario_id in pk_set:
            funcionario = instance.funcionarios.get(pk=funcionario_id)
            funcionario.atualizar_escolaridade()
            funcionario.refresh_from_db()  # Recarrega o objeto do banco após salvar


@receiver(post_save, sender=JobRotationEvaluation)
def atualizar_cargo_funcionario(sender, instance, **kwargs):
    """
    Atualiza o cargo do funcionário caso a avaliação do RH seja 'Apto'.
    """
    if instance.avaliacao_rh == "Apto" and instance.nova_funcao:
        funcionario = instance.funcionario
        funcionario.cargo_atual = instance.nova_funcao  # Atualiza o cargo atual
        funcionario.save()  # Salva as alterações no banco


@receiver(pre_save, sender=Funcionario)
def criar_historico_cargo(sender, instance, **kwargs):
    # Verifica se o cargo foi alterado
    if instance.pk:
        funcionario_antigo = Funcionario.objects.get(pk=instance.pk)

        if funcionario_antigo.cargo_atual != instance.cargo_atual:
            # Cria o histórico com o cargo que foi alterado
            HistoricoCargo.objects.create(
                funcionario=instance,
                cargo=instance.cargo_atual,  # Registra o cargo atualizado
                data_atualizacao=now(),
            )



from django.apps import AppConfig
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


CUSTOM_PERMISSOES = [
    # Qualidade de Fornecimento
    ("qualidade_fornecimento", "normatecnica", "aprovar_normatecnica", "Pode aprovar norma técnica"),
    ("qualidade_fornecimento", "relatoriof045", "f045_status", "Pode alterar status do F045"),
    ("qualidade_fornecimento", "materiaprimacatalogo", "importar_materia_prima_excel", "Pode importar matéria-prima via Excel"),
    ("qualidade_fornecimento", "relacaomateriaprima", "importar_excel_tb050", "Pode importar TB050 via Excel"),
    ("qualidade_fornecimento", "relacaomateriaprima", "selecionar_etiquetas_tb050", "Pode selecionar etiquetas do TB050"),
    ("qualidade_fornecimento", "relacaomateriaprima", "imprimir_etiquetas_tb050", "Pode imprimir etiquetas do TB050"),
    ("qualidade_fornecimento", "relacaomateriaprima", "imprimir_etiquetas_pdf", "Pode gerar PDF de etiquetas do TB050"),
    ("qualidade_fornecimento", "materiaprimacatalogo", "visualizar_materia_prima", "Pode visualizar matéria-prima"),
    ("qualidade_fornecimento", "relacaomateriaprima", "get_rolos_peso", "Pode obter peso dos rolos"),
    ("qualidade_fornecimento", "normatecnica", "norma_aprovada", "Pode verificar se norma está aprovada"),
    ("qualidade_fornecimento", "fornecedorqualificado", "relatorio_avaliacao_view", "Pode visualizar relatório de avaliação semestral"),
    ("qualidade_fornecimento", "relacaomateriaprima", "gerar_f045", "Pode gerar relatório F045"),
    ("qualidade_fornecimento", "relatoriof045", "acesso_qualidade", "Pode acessar o módulo Qualidade de Fornecimento"),
    ("qualidade_fornecimento", "relatoriof045", "dashboard_qualidade", "Pode acessar o dashboard de Qualidade de Fornecimento"),
    ("qualidade_fornecimento", "fornecedorqualificado", "importar_excel_fornecedores", "Pode importar fornecedores via Excel"),



    # Funcionário
    ("Funcionario", "avaliacaotreinamento", "imprimir_treinamento", "Pode imprimir avaliação de treinamento"),
    ("Funcionario", "listapresenca", "exportar_listas_presenca", "Pode exportar listas de presença"),
    ("Funcionario", "avaliacaoanual", "imprimir_avaliacao", "Pode imprimir avaliação anual"),
    ("Funcionario", "avaliacaoanual", "imprimir_simplificado", "Pode imprimir avaliação anual simplificada"),
    ("Funcionario", "avaliacaoexperiencia", "imprimir_avaliacao_experiencia", "Pode imprimir avaliação de experiência"),
    ("Funcionario", "jobrotationevaluation", "imprimir_jobrotation_evaluation", "Pode imprimir avaliação de Job Rotation"),
    ("Funcionario", "cargo", "imprimir_cargo", "Pode imprimir cargo"),
    ("Funcionario", "comunicado", "imprimir_comunicado", "Pode imprimir comunicado"),
    ("Funcionario", "comunicado", "imprimir_assinaturas", "Pode imprimir lista de assinaturas do comunicado"),
    ("Funcionario", "funcionario", "imprimir_ficha", "Pode imprimir ficha do funcionário"),
    ("Funcionario", "funcionario", "formulario_carta_competencia", "Pode emitir carta de competência"),
    ("Funcionario", "funcionario", "formulario_pesquisa_consciencia", "Pode emitir pesquisa de consciência"),
    ("Funcionario", "funcionario", "avaliacao_capacitacao", "Pode emitir avaliação de capacitação"),
    ("Funcionario", "funcionario", "filtro_funcionario", "Pode usar filtro de funcionário"),
    ("Funcionario", "funcionario", "filtro_carta_competencia", "Pode usar filtro da carta de competência"),
    ("Funcionario", "evento", "exportar_calendario", "Pode exportar o calendário"),
    ("Funcionario", "evento", "imprimir_calendario", "Pode imprimir o calendário"),
    ("Funcionario", "funcionario", "acesso_rh", "Pode acessar o módulo RH"),
    ("Funcionario", "cargo", "visualizar_organograma", "Pode visualizar o organograma de cargos"),
    ("metrologia", "tabelatecnica", "acesso_metrologia", "Pode acessar o módulo Metrologia"),
    ("Funcionario", "revisao", "view_revisao", "Pode visualizar descrição da revisão"),
    ("Funcionario", "integracaofuncionario", "imprimir_integracao", "Pode imprimir integração"),
    ("Funcionario", "listapresenca", "imprimir_lista_presenca", "Pode imprimir lista de presença"),
    # Relatórios RH
    ("Funcionario", "relatorio", "relatorio_indicador", "Pode acessar o Indicador de Treinamentos"),
    ("Funcionario", "relatorio", "relatorio_indicador_anual", "Pode acessar o Indicador Anual"),
    ("Funcionario", "relatorio", "cronograma_treinamentos", "Pode acessar o Cronograma de Treinamentos"),
    ("Funcionario", "relatorio", "cronograma_avaliacao_eficacia", "Pode acessar o Cronograma de Avaliação de Eficácia"),
    ("Funcionario", "relatorio", "relatorio_aniversariantes", "Pode acessar o Relatório de Aniversariantes"),


    # Formulários RH
    ("Funcionario", "funcionario", "emitir_carta_competencia", "Pode emitir carta de competência"),
    ("Funcionario", "funcionario", "emitir_pesquisa_consciencia", "Pode emitir pesquisa de consciência"),
    ("Funcionario", "funcionario", "emitir_capacitacao_pratica", "Pode emitir avaliação de capacitação prática"),
    ("Funcionario", "funcionario", "emitir_f033", "Pode emitir Solicitação de Bolsa-Treinamento (F033)"),
    ("portaria", "pessoaportaria", "acesso_portaria", "Pode acessar o módulo Portaria")


]
    

@receiver(post_migrate)
def criar_permissoes_customizadas(sender, **kwargs):
    for app_label, model, codename, name in CUSTOM_PERMISSOES:
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={"name": name}
        )
        if not created and perm.name != name:
            perm.name = name
            perm.save()
