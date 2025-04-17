import os
import sys
import django

# Adicione o diretório base do projeto ao sys.path
# Supondo que o seu manage.py esteja em C:\Projetos\RH-Qualidade\rh_qualidade
current_dir = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.join(current_dir, "..")  # sobe um nível para a pasta raiz do projeto
sys.path.insert(0, os.path.abspath(project_path))

# Define a variável de ambiente para as configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rh_qualidade.settings')

# Inicializa o Django
django.setup()

# Agora você pode importar os modelos e realizar os testes
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse

from qualidade_fornecimento.views.f045_views import gerar_f045
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.f045 import RelatorioF045

# Cria uma instância do RequestFactory para simular requisições
factory = RequestFactory()

# Obtém um usuário para a requisição (substitua "rafael.almeida" por um usuário existente)
user = User.objects.get(username='rafael.almeida')

# Escolha um ID de relação existente (por exemplo, 11)
relacao_id = 11
url = reverse("tb050_f045", args=[relacao_id])

# Exemplo de dados de POST para simular o envio do formulário
post_data = {
    # Campos do formulário principal (RelatorioF045Form)
    "qtd_carreteis": "2",
    "pedido_compra": "12345",
    "resistencia_tracao": "1500",
    "escoamento": "500",
    "alongamento": "20",
    "estriccao": "10",
    "torcao_certificado": "5",
    "dureza_certificado": "73",
    # Campos dos elementos químicos dinâmicos se houver (ex: "c_user")
    "c_user": "0.100",
    # Campo oculto para o status
    "status_geral_hidden": "Aprovado",
    # Checkbox do switch manual (simulado: o browser envia o valor "on" quando marcado)
    "switchStatusManual": "on",
    # Dados do management form do formset
    "rolos-TOTAL_FORMS": "3",
    "rolos-INITIAL_FORMS": "3",
    "rolos-MIN_NUM_FORMS": "0",
    "rolos-MAX_NUM_FORMS": "1000",
    # Dados de cada formulário inline (exemplo para 3 rolos; ajuste os nomes dos campos conforme necessário)
    "rolos-0-id": "27",
    "rolos-0-enrolamento": "OK",
    "rolos-0-dobramento": "OK",
    "rolos-0-torcao_residual": "OK",
    "rolos-0-aspecto_visual": "OK",
    "rolos-1-id": "28",
    "rolos-1-enrolamento": "OK",
    "rolos-1-dobramento": "OK",
    "rolos-1-torcao_residual": "OK",
    "rolos-1-aspecto_visual": "OK",
    "rolos-2-id": "29",
    "rolos-2-enrolamento": "OK",
    "rolos-2-dobramento": "OK",
    "rolos-2-torcao_residual": "OK",
    "rolos-2-aspecto_visual": "OK",
}

# Cria a requisição POST
request = factory.post(url, post_data)
request.user = user

# Chama a view e captura a resposta
response = gerar_f045(request, relacao_id)

# Após a execução, recarrega o objeto da relação e o F045 para verificar o status salvo
relacao = RelacaoMateriaPrima.objects.get(pk=relacao_id)
f045 = relacao.f045
print(">>> STATUS SALVO NO OBJETO F045:", f045.status_geral)
