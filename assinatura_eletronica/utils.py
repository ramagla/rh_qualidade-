import hashlib
import base64
import qrcode
import io
from django.utils.timezone import now

def gerar_assinatura(instancia, usuario):
    texto = f"{instancia._meta.label}|{instancia.pk}|{usuario.username}|{now().isoformat()}"
    return hashlib.sha256(texto.encode()).hexdigest()

def gerar_qrcode_base64(conteudo):
    img = qrcode.make(conteudo)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
