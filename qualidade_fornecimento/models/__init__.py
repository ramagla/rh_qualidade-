# qualidade_fornecimento/models/__init__.py — PARA
from .controle_servico_externo import ControleServicoExterno, RetornoDiario
from .f045 import RelatorioF045
from .fornecedor import FornecedorQualificado
from .inspecao_servico_externo import InspecaoServicoExterno

# Catálogo / TB050
from .materiaPrima import RelacaoMateriaPrima
from .materiaPrima_catalogo import MateriaPrimaCatalogo

# ✅ Rolo — exporta o modelo correto
from .rolo import RoloMateriaPrima
# (opcional p/ retrocompatibilidade com algum código antigo)
RelacaoMateriaPrimaRolo = RoloMateriaPrima

# Normas
from .norma import NormaComposicaoElemento, NormaTecnica, NormaTracao

# Inventário
from .inventario import (
    Inventario,
    InventarioItem,
    Contagem,
    Divergencia,
    InventarioExportacao,
)

# Estoque Intermediário
from .estoque_intermediario import EstoqueIntermediario
