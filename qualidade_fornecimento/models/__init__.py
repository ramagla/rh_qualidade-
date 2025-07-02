from .controle_servico_externo import ControleServicoExterno, RetornoDiario
from .f045 import RelatorioF045
from .fornecedor import FornecedorQualificado
from .inspecao_servico_externo import InspecaoServicoExterno
from .materiaPrima import RelacaoMateriaPrima
from .materiaPrima_catalogo import (  # Certifique-se de que essa importação esteja correta
    MateriaPrimaCatalogo,
)
from .norma import NormaComposicaoElemento, NormaTecnica, NormaTracao
from .rolo import RelacaoMateriaPrima
from .inspecao10 import Inspecao10, DevolucaoServicoExterno