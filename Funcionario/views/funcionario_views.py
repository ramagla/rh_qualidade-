# Django - Funcionalidades principais
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

# App Interno
from Funcionario.forms import FuncionarioForm
from Funcionario.models import Funcionario, HistoricoCargo
from Funcionario.models.cargo import Cargo
from Funcionario.utils.funcionario_utils import (
    filtrar_funcionarios,
    obter_contexto_funcionario,
    gerar_mensagem_acesso_texto,
    montar_estrutura_organograma,
)
from Funcionario.models import (    
    Treinamento,
)


@login_required
def lista_funcionarios(request):
    funcionarios = filtrar_funcionarios(request)
    paginator = Paginator(funcionarios, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    status = request.GET.get("status", "Ativo")
    context = obter_contexto_funcionario(funcionarios, status, page_obj)
    return render(request, "funcionarios/lista_funcionarios.html", context)


@login_required
def visualizar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    context = {"funcionario": funcionario, "now": timezone.now()}

    if funcionario.responsavel:
        responsavel = Funcionario.objects.filter(nome=funcionario.responsavel).first()
        context["cargo_responsavel"] = (
            responsavel.cargo_responsavel if responsavel else "Cargo não encontrado"
        )
    return render(request, "funcionarios/visualizar_funcionario.html", context)


@login_required
def cadastrar_funcionario(request):
    form = FuncionarioForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Funcionário cadastrado com sucesso!")
        return redirect("lista_funcionarios")
    return render(request, "funcionarios/form_funcionario.html", {"form": form})


@login_required
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    form = FuncionarioForm(request.POST or None, request.FILES or None, instance=funcionario)

    if request.method == "POST" and form.is_valid():
        # ✅ remover CURRÍCULO se marcado
        print("remover_curriculo:", request.POST.get("remover_curriculo"))
        print("remover_formulario_f146:", request.POST.get("remover_formulario_f146"))
        if request.POST.get("remover_curriculo") == "1" and funcionario.curriculo:
            funcionario.curriculo.delete(save=False)  # apaga do storage
            funcionario.curriculo = None              # zera o campo no model

        # ✅ remover CERTIFICADO se marcado
        if request.POST.get("remover_formulario_f146") == "1" and funcionario.formulario_f146:
            funcionario.formulario_f146.delete(save=False)
            funcionario.formulario_f146 = None

        # ✅ agora aplica demais alterações do form
        form.save()
        messages.success(request, "Funcionário editado com sucesso!")
        return redirect("lista_funcionarios")

    responsaveis = Funcionario.objects.exclude(id=funcionario_id)
    return render(
        request,
        "funcionarios/form_funcionario.html",
        {"form": form, "funcionario": funcionario, "responsaveis": responsaveis},
    )




@login_required
def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if Treinamento.objects.filter(funcionarios=funcionario).exists():
        funcionario.status = "Inativo"
        funcionario.save(update_fields=["status"])
        messages.success(request, "Funcionário foi marcado como Inativo.")
    else:
        funcionario.delete()
        messages.success(request, "Funcionário excluído com sucesso.")
    return redirect("lista_funcionarios")


class ImprimirFichaView(View):
    def get(self, request, funcionario_id):
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        context = montar_estrutura_organograma(funcionario)
        return render(request, "funcionarios/template_de_impressao.html", context)

    def post(self, request, funcionario_id):
        return self.get(request, funcionario_id)


@login_required
def listar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    historicos = HistoricoCargo.objects.filter(funcionario=funcionario).order_by("-data_atualizacao")
    return render(request, "funcionarios/historico_cargo.html", {"funcionario": funcionario, "historicos": historicos})


@login_required
def adicionar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == "POST":
        cargo = get_object_or_404(Cargo, id=request.POST.get("cargo"))
        HistoricoCargo.objects.create(
            funcionario=funcionario,
            cargo=cargo,
            data_atualizacao=request.POST.get("data_atualizacao"),
        )
        messages.success(request, "Histórico de cargo adicionado com sucesso.")
        return redirect("listar_historico_cargo", funcionario_id=funcionario.id)
    cargos = Cargo.objects.all()
    return render(request, "funcionarios/adicionar_historico_cargo.html", {"funcionario": funcionario, "cargos": cargos})


@login_required
def excluir_historico_cargo(request, historico_id):
    historico = get_object_or_404(HistoricoCargo, id=historico_id)
    historico.delete()
    return redirect("listar_historico_cargo", funcionario_id=historico.funcionario.id)


@login_required
def gerar_mensagem_acesso(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    mensagem = gerar_mensagem_acesso_texto(funcionario)
    return render(request, "funcionarios/mensagem_acesso.html", {"mensagem": mensagem, "funcionario": funcionario})


@login_required
def selecionar_funcionario_mensagem_acesso(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(request, "funcionarios/selecionar_mensagem_acesso.html", {"funcionarios": funcionarios})


@login_required
def gerar_mensagem_acesso_redirect(request):
    funcionario_id = request.GET.get("funcionario_id")
    if funcionario_id:
        return redirect("gerar_mensagem_acesso", funcionario_id=funcionario_id)
    return redirect("selecionar_funcionario_mensagem_acesso")



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from Funcionario.models import Funcionario

def somente_digitos(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

@login_required
def gerar_assinatura_email(request, funcionario_id: int):
    func = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == "POST":
        ramal = (request.POST.get("ramal") or "").strip()
        celular = (request.POST.get("celular") or "").strip()
        linkedin = (request.POST.get("linkedin") or "").strip()

        whatsapp_digits = somente_digitos(celular)
        wa_link = f"https://wa.me/{whatsapp_digits}" if whatsapp_digits else ""

        # Função para formatar exibição do celular
        def formatar_celular(digits: str) -> str:
            # esperado: 55 + DDD (2) + numero (9 dígitos)
            if len(digits) == 13 and digits.startswith("55"):
                ddd = digits[2:4]
                numero = digits[4:]
                return f"+55 ({ddd}) {numero[:5]}-{numero[5:]}"
            return digits  # fallback, caso venha em formato inesperado

        celular_fmt = formatar_celular(whatsapp_digits)
        nome = escape(getattr(func, "nome", "") or "")

        # Cargo por FK: usamos apenas cargo.nome e numero_dc
        cargo_obj = getattr(func, "cargo_atual", None) or getattr(func, "cargo_inicial", None)
        cargo_nome = (cargo_obj.nome if cargo_obj and getattr(cargo_obj, "nome", None) else "").strip()
        cargo_numero_dc = (cargo_obj.numero_dc if cargo_obj and getattr(cargo_obj, "numero_dc", None) else "")
        # Oculta se numero_dc == 61
        ocultar_cargo = str(cargo_numero_dc).zfill(2) == "61"
        cargo_html = "" if ocultar_cargo or not cargo_nome else f'<div style="font-size:13px;color:#475569">{escape(cargo_nome)}</div>'

        # Nome com/sem link do LinkedIn
        if linkedin:
            nome_anchor = f'<a href="{escape(linkedin)}" style="color:#0f172a;text-decoration:none" target="_blank">{nome}</a>'
        else:
            nome_anchor = f'<span style="color:#0f172a;text-decoration:none">{nome}</span>'

        email = escape(getattr(getattr(func, "user", None), "email", "") or "")
        empresa = "Bras-Mol Molas e Estampados Ltda"
        static_base = "https://qualidade.brasmol.com.br/static/assinatura_email"

        assinatura_html = f"""
<table cellpadding="0" cellspacing="0" width="600" style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#0f172a;line-height:1.35;max-width:600px;width:100%">
  <tr>
    <td style="padding:16px 12px">
      <table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;background:#fff">
        <tr>
          <td valign="top" width="58%" style="padding:16px 12px 12px 16px">
            <div style="font-size:20px;font-weight:bold">{nome_anchor}</div>
            {cargo_html}
            <div style="font-size:12px;color:#475569">{empresa}</div>
            <table style="margin-top:10px">
              <tr>
                <td><img src="{static_base}/ic-email.png" width="16"></td>
                <td><a href="mailto:{email}" style="color:#0f172a;text-decoration:none">{email}</a></td>
              </tr>
              <tr>
                <td><img src="{static_base}/ic-phone.png" width="16"></td>
                <td>
                  +55 (11) 4648-2611{f" · Ramal {escape(ramal)}" if ramal else ""}
{f"<br><a href='{wa_link}' style='color:#0f172a;text-decoration:none'>{celular_fmt} <img src='{static_base}/ic-whatsapp.png' width='14' style='vertical-align:middle'></a>" if whatsapp_digits else ""}
                </td>
              </tr>
              <tr>
                <td><img src="{static_base}/ic-web.png" width="16"></td>
                <td><a href="https://www.brasmol.com.br" style="color:#0f172a;text-decoration:none">www.brasmol.com.br</a></td>
              </tr>
              <tr>
                <td><img src="{static_base}/ic-linkedin.png" width="16"></td>
                <td><a href="https://www.linkedin.com/company/brasmol/" style="color:#0f172a;text-decoration:none">LinkedIn — Bras-Mol</a></td>
              </tr>
              <tr>
                <td><img src="{static_base}/ic-map.png" width="16"></td>
                <td><a href="https://maps.google.com/?q=Estrada+do+Bonsucesso,+1953,+Itaquaquecetuba" style="color:#475569;text-decoration:none">Estrada do Bonsucesso, 1953 — Itaquaquecetuba/SP</a></td>
              </tr>
              <tr>
                <td><img src="{static_base}/ic-link.png" width="16"></td>
                <td><a href="https://montagem.brasmol.com.br" style="color:#0f172a;text-decoration:none">Conheça nossa linha de montagem</a></td>
              </tr>
            </table>
          </td>
          <td valign="middle" width="42%" style="background:#f9fafb;text-align:center">
            <img src="{static_base}/logo.png" width="150">
            <div style="font-size:12px;color:#0f172a;font-weight:bold;margin-top:6px">Tecnologia e Qualidade</div>
          </td>
        </tr>
      </table>
      <div style="font-size:11px;color:#6b7280;margin-top:6px">Esta mensagem é confidencial. Se recebida por engano, apague e avise o remetente. <a href="{static_base}/politica_de_privacidade.pdf" style="color:#6b7280">Política de privacidade</a></div>
    </td>
  </tr>
</table>
        """.strip()

        # Minimiza (remove quebras e espaços duplicados)
        assinatura_min = " ".join(assinatura_html.split())

        return render(
            request,
            "funcionarios/assinatura_resultado.html",
            {
                "funcionario": func,
                "assinatura_html": assinatura_min,
                "ramal": ramal,
                "celular": celular,
                "linkedin": linkedin,
            },
        )

    # GET -> formulário
    return render(request, "funcionarios/assinatura_form.html", {"funcionario": func})
