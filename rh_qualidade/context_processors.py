# rh_qualidade/context_processors.py

def default_form(request):
    """
    Garante que a variável `form` exista em todos os templates,
    valendo None quando não for passada pela view.
    """
    return {"form": None}
