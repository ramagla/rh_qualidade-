import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    # 1) Extrai só o nome do arquivo
    base = os.path.basename(value)
    name, ext = os.path.splitext(base)
    # 2) Remove o sufixo após o último underscore
    if "_" in name:
        name = name.rsplit("_", 1)[0]
    # 3) Opcional: substituir underlines por espaços e capitalizar
    # name = " ".join(w.capitalize() for w in name.split("_"))
    return f"{name}{ext}"