from collections import ChainMap

from .funcionario import funcionario_permissions
from .metrologia import metrologia_permissions
from .qualidade_fornecimento import qualidade_permissions
from .portaria import portaria_permissions
from .comercial import comercial_permissions
from .recibos import recibos_permissions  # ✅ novo import
from .tecnico import tecnico_permissions

# Combina todos os dicionários de permissões em um só
permission_map = dict(ChainMap(
    funcionario_permissions,
    metrologia_permissions,
    qualidade_permissions,
    portaria_permissions,  # ✅ novo
    comercial_permissions,  # ✅ novo
    portaria_permissions, 
    recibos_permissions,  
    tecnico_permissions,
))
