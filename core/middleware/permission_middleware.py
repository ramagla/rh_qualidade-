from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.http import HttpResponseServerError
from .permissions.mapa_completo import permission_map


# ✅ Views públicas (basenames, com ou sem namespace)
PUBLIC_VIEW_BASENAMES = {
    "responder_cotacao_materia_prima",
    "responder_cotacao_servico_lote",
}

# ✅ Prefixos públicos por caminho (fallback — ajuste se necessário)
PUBLIC_PATH_PREFIXES = (
    "/comercial/precalculo/materia/",
    "/comercial/precalculo/servicos/",
    "/comercial/precalculo/servico",   # inclua '/servicos/' se for o seu path real
)

def redirecionar_para_modulo_permitido(user):
    if user.has_perm("qualidade_fornecimento.acesso_qualidade"):
        return redirect("qualidadefornecimento_home")
    if user.has_perm("metrologia.acesso_metrologia"):
        return redirect("metrologia_home")
    if user.has_perm("Funcionario.acesso_rh"):
        return redirect("home")
    if user.has_perm("tecnico.acesso_tecnico"):
        return redirect("tecnico:tecnico_home")
    return redirect("acesso_negado")


class PermissionMiddleware:
    """
    Libera explicitamente as views públicas de cotação ANTES de exigir login.
    Posicionamento: após AuthenticationMiddleware e antes de XFrameOptionsMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.paths_livres = {
            "/login/",
            "/senha/esqueci/",
            "/senha/enviado/",
            "/senha/finalizado/",
            "/senha/nova/",
            "/assinatura/validar/",
        }

    def __call__(self, request):
        # 0) Fallback por caminho: libera prefixos públicos
        if any(request.path.startswith(p) for p in PUBLIC_PATH_PREFIXES):
            resp = self.get_response(request)
            return resp or HttpResponseServerError("Handler retornou None (rota pública por path).")

        # 1) Resolve o nome da view (mesmo para usuário anônimo)
        try:
            view_name = resolve(request.path_info).view_name
        except Resolver404:
            view_name = None

        # 2) Se a view é pública (com ou sem namespace), libera
        base_name = view_name.split(":", 1)[-1] if view_name else None
        if base_name in PUBLIC_VIEW_BASENAMES:
            resp = self.get_response(request)
            return resp or HttpResponseServerError("Handler retornou None (view pública).")

        # 3) Regras para anônimo (mantém rotas livres de auth)
        if not request.user.is_authenticated:
            if any(request.path.startswith(p) for p in self.paths_livres):
                resp = self.get_response(request)
                return resp or HttpResponseServerError("Handler retornou None (rota livre auth).")
            return redirect("login")

        # 4) Checagem de permissão mapeada
        if view_name:
            required_permission = permission_map.get(view_name)
            if required_permission and not request.user.has_perm(required_permission):
                return redirect("acesso_negado")

        # 5) Fluxo normal com guarda contra None
        resp = self.get_response(request)
        return resp or HttpResponseServerError("Handler retornou None (verifique sua view).")
