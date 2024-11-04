from django.http import JsonResponse
from Funcionario.models import Cargo, Funcionario, Treinamento, ListaPresenca

def get_funcionario_info(request, id):
    try:
        funcionario = Funcionario.objects.get(id=id)
        data = {
            'nome': funcionario.nome,
            'local_trabalho': funcionario.local_trabalho,
            'cargo_atual': funcionario.cargo_atual.nome if funcionario.cargo_atual else '',
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado'}, status=404)

def get_treinamentos(request, funcionario_id):
    treinamentos = Treinamento.objects.filter(funcionario_id=funcionario_id).values('tipo', 'nome_curso', 'categoria')
    return JsonResponse(list(treinamentos), safe=False)

def get_competencias(request):
    try:
        competencias = Cargo.objects.all()
        competencias_data = []

        for competencia in competencias:
            # Tente buscar a última revisão; se não houver, registre um valor padrão
            ultima_revisao = competencia.revisoes.order_by('-data_revisao').first()
            competencias_data.append({
                "id": competencia.id,
                "numero_dc": competencia.numero_dc,
                "nome": competencia.nome,
                "numero_revisao": ultima_revisao.numero_revisao if ultima_revisao else "Sem revisão",
                "data_revisao": ultima_revisao.data_revisao.strftime("%d/%m/%Y") if ultima_revisao else "Sem data"
            })

        return JsonResponse(competencias_data, safe=False)

    except Exception as e:
        # Log detalhado para análise de erro
        print(f"Erro ao carregar competências: {e}")
        return JsonResponse({"error": f"Erro ao carregar as competências: {e}"}, status=500)

def get_cargo(request, funcionario_id):
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
        data = {
            'cargo': funcionario.cargo_atual.nome if funcionario.cargo_atual else 'Cargo não encontrado',
            'departamento': funcionario.local_trabalho or 'Departamento não encontrado',
            'responsavel': funcionario.responsavel or 'Responsável não encontrado'
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse({
            'cargo': 'Não encontrado', 
            'departamento': 'Não encontrado',
            'responsavel': 'Não encontrado'
        }, status=404)


from django.http import JsonResponse
from Funcionario.models import Funcionario, Treinamento, AvaliacaoTreinamento, AvaliacaoDesempenho, JobRotationEvaluation



def get_funcionario_ficha(request, id):
    try:
        funcionario = Funcionario.objects.get(id=id)

        # Coletando informações básicas do funcionário
        data = {
            'nome': funcionario.nome,
            'data_admissao': funcionario.data_admissao,
            'cargo_atual': funcionario.cargo_atual.nome if funcionario.cargo_atual else '',
            'local_trabalho': funcionario.local_trabalho,
            'escolaridade': funcionario.escolaridade,
            'status': funcionario.status,
            'foto': funcionario.foto.url if funcionario.foto else None,
            'curriculo': funcionario.curriculo.url if funcionario.curriculo else None,
        }

        # Avaliações de Desempenho
        avaliacoes_desempenho = AvaliacaoDesempenho.objects.filter(funcionario=funcionario).values(
            'data_avaliacao',
            'centro_custo',
            'gerencia',
            'avaliador__nome',
            'postura_seg_trabalho',
            'qualidade_produtividade',
            'trabalho_em_equipe',
            'comprometimento',
            'disponibilidade_para_mudancas',
            'disciplina',
            'rendimento_sob_pressao',
            'proatividade',
            'comunicacao',
            'assiduidade',
            'observacoes'
        )
        data['avaliacoes_desempenho'] = list(avaliacoes_desempenho)

        # Avaliações de Treinamento
        avaliacoes_treinamento = AvaliacaoTreinamento.objects.filter(funcionario=funcionario).select_related('treinamento').values(
            'data_avaliacao',
            'treinamento__id',  # ID do treinamento
            'treinamento__assunto',  # Acesso ao assunto do treinamento através da relação correta
            'responsavel_1_nome',
            'responsavel_2_nome',
            'responsavel_3_nome',
            'avaliacao_geral'
        )
        data['avaliacoes_treinamento'] = list(avaliacoes_treinamento)

        # Treinamentos
        treinamentos = Treinamento.objects.filter(funcionario=funcionario).values(
            'tipo',
            'nome_curso',
            'categoria',
            'data_inicio',
            'data_fim',
            'status'
        )
        data['treinamentos'] = list(treinamentos)

        # Avaliações de Job Rotation
        job_rotations = JobRotationEvaluation.objects.filter(funcionario=funcionario).values(
            'area_atual',
            'nova_funcao__nome',
            'data_inicio',
            'termino_previsto',
            'avaliacao_gestor',
            'avaliacao_funcionario',
            'avaliacao_rh'
        )
        data['job_rotations'] = list(job_rotations)

        return JsonResponse(data, safe=False)

    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado'}, status=404)
