# Funcionario/views/__init__.py

from .cargos_views import (
    lista_cargos,
    cadastrar_cargo,
    editar_cargo,
    excluir_cargo,  # Certifique-se de que esta linha está presente
    historico_revisoes,
    adicionar_revisao,
    excluir_revisao,   
)

from .home_views import sucesso_view
from .api_views import get_competencias
