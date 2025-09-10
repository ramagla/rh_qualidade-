from .controle_servico_externo import ControleServicoExterno, RetornoDiario
from .f045 import RelatorioF045
from .fornecedor import FornecedorQualificado
from .inspecao_servico_externo import InspecaoServicoExterno

# ✅ Mantém o nome canônico usado nas views antigas:
from .materiaPrima import RelacaoMateriaPrima
from .materiaPrima_catalogo import MateriaPrimaCatalogo

from .norma import NormaComposicaoElemento, NormaTecnica, NormaTracao

# ✅ Evita colisão: exporta o model de rolo com outro nome
from .rolo import RelacaoMateriaPrima as RelacaoMateriaPrimaRolo

# ✅ Inventário: exporta todas as classes usadas nas novas views
from .inventario import (
    Inventario,
    InventarioItem,
    Contagem,
    Divergencia,
    InventarioExportacao,
)
