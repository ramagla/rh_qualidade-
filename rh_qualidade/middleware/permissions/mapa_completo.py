from collections import ChainMap

from .funcionario import funcionario_permissions
from .metrologia import metrologia_permissions
from .qualidade_fornecimento import qualidade_permissions
from .portaria import portaria_permissions


# Combina todos os dicionários de permissões em um só
permission_map = dict(ChainMap(
    funcionario_permissions,
    metrologia_permissions,
    qualidade_permissions,
    portaria_permissions,  # ✅ novo

))
