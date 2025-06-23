import fitz  # PyMuPDF
from decimal import Decimal
import re

def extrair_valores_recibo_bytes(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = "\n".join(page.get_text() for page in doc)
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    print("\n🧪 [PROCESSANDO LINHAS PARA EXTRAÇÃO]:\n")
    for i, linha in enumerate(linhas):
        print(f"{i:03d}: {linha}")

    # Encontra o índice da frase final que antecede os valores
    idx_base = -1
    for i, linha in enumerate(linhas):
        if "recebido a importância líquida" in linha:
            idx_base = i
            break

    valores = []
    if idx_base != -1:
        for l in linhas[idx_base + 1:]:
            if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", l):
                valores.append(Decimal(l.replace('.', '').replace(',', '.')))
                if len(valores) == 3:
                    break

    if len(valores) == 3:
        valor_total, valor_descontos, valor_liquido = valores
    else:
        valor_total = valor_descontos = valor_liquido = None

    resultado = {
        "valor_total": valor_total,
        "valor_descontos": valor_descontos,
        "valor_liquido": valor_liquido,
    }

    print("\n📦 [RESULTADO FINAL EXTRAÍDO]:")
    print(resultado)
    return resultado

# Teste local
if __name__ == "__main__":
    caminho = "C:/Projetos/RH-Qualidade/rh_qualidade/templates/93-03-2025-M-847-DOUGLASPEREIRASIQUEIRA-Recibo de Pagamento.pdf"
    try:
        with open(caminho, "rb") as f:
            pdf_bytes = f.read()
            extrair_valores_recibo_bytes(pdf_bytes)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho}")
    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")
