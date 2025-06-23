# rh_qualidade/rh_qualidade/recibos_views.py

# rh_qualidade/rh_qualidade/recibos_views.py

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from Funcionario.models.recibos import ReciboPagamento
from Funcionario.models import Funcionario

from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from Funcionario.models import Funcionario
from Funcionario.models.recibos import ReciboPagamento

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum
from Funcionario.models.recibos import ReciboPagamento
from Funcionario.models import Funcionario
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from collections import OrderedDict
from Funcionario.models import Funcionario
from Funcionario.models.recibos import ReciboPagamento

@login_required
@permission_required('Funcionario.view_recibopagamento', raise_exception=True)
def recibos_pagamento(request):
    user = request.user
    nome = request.GET.get("nome")
    mes_ano = request.GET.get("mes")  # Ex: "03/2025"

    # Base queryset
    if user.username == 'rafael.almeida' or user.is_superuser:
        recibos = ReciboPagamento.objects.select_related('funcionario').all()
    else:
        try:
            funcionario = user.funcionario
            recibos = ReciboPagamento.objects.filter(funcionario=funcionario)
        except Funcionario.DoesNotExist:
            recibos = ReciboPagamento.objects.none()

    # Filtro por nome do colaborador
    if nome:
        recibos = recibos.filter(nome_colaborador__icontains=nome)

    # Filtro por mês/ano
    if mes_ano and "/" in mes_ano:
        mes_str, ano_str = mes_ano.split("/")
        try:
            mes = int(mes_str)
            ano = int(ano_str)
            recibos = recibos.filter(mes_referencia__month=mes, mes_referencia__year=ano)
        except ValueError:
            pass

    # Indicadores
    total_liquido = recibos.aggregate(total=Sum('valor_liquido'))['total'] or 0
    total_vencimentos = recibos.aggregate(total=Sum('valor_total'))['total'] or 0
    total_descontos = recibos.aggregate(total=Sum('valor_descontos'))['total'] or 0

    # Paginação
    paginator = Paginator(recibos.order_by('-mes_referencia'), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Lista de funcionários filtrada
    funcionarios_unicos = Funcionario.objects.filter(
        id__in=recibos.values_list("funcionario_id", flat=True)
    ).order_by("nome")

    # Geração dinâmica de opções de mês/ano disponíveis
    meses_disponiveis = ReciboPagamento.objects \
        .annotate(mes=TruncMonth("mes_referencia")) \
        .values_list("mes", flat=True) \
        .distinct() \
        .order_by("mes")

    opcoes_mes_ano = OrderedDict()
    for data in meses_disponiveis:
        chave = data.strftime("%m/%Y")
        opcoes_mes_ano[chave] = chave

    return render(request, 'recibos/recibos_pagamento.html', {
        'page_obj': page_obj,
        'total_liquido': total_liquido,
        'total_vencimentos': total_vencimentos,
        'total_descontos': total_descontos,
        'funcionarios': funcionarios_unicos,
        'filtro_nome': nome or '',
        'filtro_mes': mes_ano or '',
        'opcoes_mes_ano': opcoes_mes_ano,
    })




import os
import zipfile
import tempfile
from datetime import datetime
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from Funcionario.models import Funcionario
from Funcionario.models.recibos import ReciboPagamento


from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.contrib import messages
from django.core.files.base import ContentFile
from datetime import datetime
import os, zipfile, tempfile
from decimal import Decimal
import fitz  # PyMuPDF
import re

from Funcionario.models import Funcionario
from Funcionario.models.recibos import ReciboPagamento


import zipfile
from django.shortcuts import redirect
from django.contrib import messages
from django.core.files.base import ContentFile
from io import BytesIO
from .utils import extrair_valores_recibo  # ou o local onde salvou a função

@require_POST
@permission_required('Funcionario.importar_recibo_pagamento', raise_exception=True)
def importar_zip_recibos(request):
    from .utils import extrair_valores_recibo  # Certifique-se de que está no local correto

    zip_file = request.FILES.get('arquivo_zip')

    if not zip_file or not zip_file.name.endswith('.zip'):
        messages.error(request, "Por favor, envie um arquivo .zip válido.")
        return redirect('recibos_pagamento')

    print(f"[INFO] ZIP recebido: {zip_file.name}")

    with tempfile.TemporaryDirectory() as tmpdirname:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)

        for root, _, files in os.walk(tmpdirname):
            for filename in files:
                if not filename.lower().endswith('.pdf'):
                    print(f"[IGNORADO] {filename} não é PDF.")
                    continue

                print(f"[DEBUG] Processando: {filename}")
                nome_arquivo = filename.replace(".pdf", "")
                partes = nome_arquivo.split('-')

                if len(partes) < 5:
                    print(f"[ERRO] Nome inválido: {filename}")
                    continue

                try:
                    mes = int(partes[1])
                    ano = int(partes[2])
                    numero = partes[4].strip()
                    mes_referencia = datetime(ano, mes, 1).date()
                except Exception as e:
                    print(f"[ERRO] Falha ao interpretar nome do arquivo: {e}")
                    continue

                # Tenta encontrar funcionário por número de registro ou número do recibo
                # Tenta encontrar funcionário primeiro por número de registro do recibo, depois por número de registro normal
                funcionario = Funcionario.objects.filter(numero_registro_recibo=numero).first()
                if not funcionario:
                    print(f"[ERRO] Funcionário com número de recibo '{numero}' não encontrado.")
                    continue



                if not funcionario:
                    print(f"[ERRO] Funcionário '{numero}' não encontrado.")
                    continue

                # Evita duplicidade de recibo por mês
                if ReciboPagamento.objects.filter(funcionario=funcionario, mes_referencia=mes_referencia).exists():
                    print(f"[IGNORADO] Recibo já existe para {funcionario.nome} - {mes_referencia}")
                    continue

                try:
                    caminho_arquivo = os.path.join(root, filename)
                    with open(caminho_arquivo, 'rb') as f:
                        content = f.read()

                    dados = extrair_valores_recibo(content)
                    print(f"[DADOS EXTRAÍDOS] {dados}")  # DEBUG

                    recibo = ReciboPagamento.objects.create(
                        funcionario=funcionario,
                        nome_colaborador=funcionario.nome,
                        mes_referencia=mes_referencia,
                        valor_total=dados.get("valor_total"),
                        valor_descontos=dados.get("valor_descontos"),
                        valor_liquido=dados.get("valor_liquido"),
                    )
                    recibo.arquivo_pdf.save(filename, ContentFile(content), save=True)

                    print(f"[SUCESSO] Recibo salvo para {funcionario.nome}")

                except Exception as e:
                    print(f"[FALHA] Erro ao processar {filename}: {e}")
                    continue

    messages.success(request, "Recibos importados com sucesso!")
    return redirect('recibos_pagamento')
