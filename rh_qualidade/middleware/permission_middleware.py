from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.core.exceptions import PermissionDenied

from .permissions.mapa_completo import permission_map


def redirecionar_para_modulo_permitido(user):
    if user.has_perm("qualidade_fornecimento.acesso_qualidade"):
        return redirect("qualidadefornecimento_home")
    elif user.has_perm("metrologia.acesso_metrologia"):
        return redirect("metrologia_home")
    elif user.has_perm("Funcionario.acesso_rh"):
        return redirect("home")
    return redirect("acesso_negado")


class PermissionMiddleware:
    """
    Middleware para verificar autenticação e permissões com base nas URLs acessadas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rotas públicas que podem ser acessadas sem autenticação
        paths_livres = [
            "/login/",
            "/senha/esqueci/",
            "/senha/enviado/",
            "/senha/finalizado/",
            "/senha/nova/",  # cobre /senha/nova/<uidb64>/<token>/
        ]

        if not request.user.is_authenticated:
            if any(request.path.startswith(p) for p in paths_livres):
                return self.get_response(request)
            return redirect("login")

        try:
            resolver_match = resolve(request.path)
            view_name = resolver_match.view_name
        except Resolver404:
            return self.get_response(request)

        # Verifica permissão necessária para a view
        required_permission = permission_map.get(view_name)
        if required_permission and not request.user.has_perm(required_permission):
            return redirect("acesso_negado")  # ou: raise PermissionDenied()

        return self.get_response(request)
