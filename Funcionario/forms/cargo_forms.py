from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django_select2.forms import Select2Widget

from rh_qualidade.utils import title_case

from ..models import Cargo, Funcionario, Revisao


class CargoForm(forms.ModelForm):
    """
    Formulário de cadastro e edição de cargos.
    Usa CKEditor para campos textuais e Select2 para seleção de elaborador/aprovador.
    Filtra apenas funcionários ativos para elaborador/aprovador.
    Aplica title_case no nome e strip no número do documento.
    """
    responsabilidade_atividade_primaria = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Descreva as principais responsabilidades e autoridade"}
        ),
        required=True
    )
    responsabilidade_atividade_secundaria = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Descreva as responsabilidades secundárias, se houver"}
        ),
        required=True
    )
    educacao_minima = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Informe o grau mínimo de escolaridade exigido"}
        ),
        required=True
    )
    treinamento_externo = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Cursos ou treinamentos externos recomendados"}
        ),
        required=True
    )
    treinamento_interno_minimo = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Formações internas exigidas para a função"}
        ),
        required=True
    )
    experiencia_minima = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Tempo e tipo de experiência mínima necessária"}
        ),
        required=True
    )

    class Meta:
        model = Cargo
        fields = [
            "nome",
            "numero_dc",
            "descricao_arquivo",
            "departamento",
            "responsabilidade_atividade_primaria",
            "responsabilidade_atividade_secundaria",
            "educacao_minima",
            "treinamento_externo",
            "treinamento_interno_minimo",
            "experiencia_minima",
            "elaborador",
            "elaborador_data",
            "aprovador",
            "aprovador_data",
            "nivel",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "numero_dc": forms.TextInput(attrs={"class": "form-control"}),
            "descricao_arquivo": forms.FileInput(attrs={"class": "form-control"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "nivel": forms.Select(attrs={"class": "form-select"}),
            "elaborador": Select2Widget(attrs={
                "class": "form-select select2",
                "data-dropdown-parent": "#collapseAprovacao"
            }),
            "aprovador": Select2Widget(attrs={
                "class": "form-select select2",
                "data-dropdown-parent": "#collapseAprovacao"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar funcionários ativos para elaborador e aprovador
        ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")
        self.fields["elaborador"].queryset = ativos
        self.fields["aprovador"].queryset = ativos
        self.fields["departamento"].widget.attrs.update({"class": "form-select select2"})

        # Definir valores padrão se novo cadastro
        if not self.instance.pk:
            try:
                self.fields["elaborador"].initial = Funcionario.objects.get(
                    nome="Anderson Goveia de Lacerda"
                ).id
            except Funcionario.DoesNotExist:
                self.fields["elaborador"].initial = None
            try:
                self.fields["aprovador"].initial = Funcionario.objects.get(
                    nome="Lilian Fernandes"
                ).id
            except Funcionario.DoesNotExist:
                self.fields["aprovador"].initial = None

    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "")
        if nome:
            return title_case(nome)
        return nome

    def clean_numero_dc(self):
        numero_dc = self.cleaned_data.get("numero_dc", "")
        return numero_dc.strip()

    def clean_descricao_arquivo(self):
        f = self.cleaned_data.get("descricao_arquivo")
        if f and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("O arquivo excede 5 MB.")
        return f

class RevisaoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de revisões de cargo.
    Usa CKEditor para a descrição da mudança.
    """
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = Revisao
        fields = ["numero_revisao", "data_revisao", "descricao_mudanca"]
        widgets = {
            "numero_revisao": forms.TextInput(attrs={"class": "form-control"}),
            "data_revisao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def clean_numero_revisao(self):
        numero_revisao = self.cleaned_data.get("numero_revisao", "")
        return numero_revisao.title()

    def clean_descricao_mudanca(self):
        descricao_mudanca = self.cleaned_data.get("descricao_mudanca", "")
        return descricao_mudanca.strip()
