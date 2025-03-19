# Funcionario/views/__init__.py

from .api_views import get_competencias
from .cargos_views import excluir_cargo  # Certifique-se de que esta linha está presente
from .cargos_views import (
    adicionar_revisao,
    cadastrar_cargo,
    editar_cargo,
    excluir_revisao,
    historico_revisoes,
    lista_cargos,
)
from .home_views import sucesso_view
