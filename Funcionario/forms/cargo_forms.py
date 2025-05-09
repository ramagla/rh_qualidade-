from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django_select2.forms import Select2Widget

from rh_qualidade.utils import title_case

from ..models import Cargo, Funcionario, Revisao


class CargoForm(forms.ModelForm):
    # Definindo os campos com CKEditor5Widget
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
            "departamento": forms.TextInput(attrs={"class": "form-control"}),
            "nivel": forms.Select(attrs={"class": "form-select"}),  # 👈 Aqui

            "elaborador": Select2Widget(attrs={"class": "form-select"}),
            "elaborador_data": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "aprovador": Select2Widget(attrs={"class": "form-select"}),
            "aprovador_data": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar funcionários ativos e ordenar alfabeticamente
        self.fields["elaborador"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")
        self.fields["aprovador"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")

        # Definir valores padrão se o formulário for novo
        if not self.instance.pk:
            try:
                self.fields["elaborador"].initial = Funcionario.objects.get(
                    nome="Anderson Goveia de Lacerda"
                ).id
            except Funcionario.DoesNotExist:
                # Deixa em branco se não encontrar
                self.fields["elaborador"].initial = None

            try:
                self.fields["aprovador"].initial = Funcionario.objects.get(
                    nome="Lilian Fernandes"
                ).id
            except Funcionario.DoesNotExist:
                # Deixa em branco se não encontrar
                self.fields["aprovador"].initial = None

    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "")
        if nome:
            return title_case(nome)  # Aplica a função title_case personalizada
        return nome

    def clean_numero_dc(self):
        numero_dc = self.cleaned_data.get("numero_dc", "")
        return numero_dc.strip()  # Apenas exemplo para limpar espaços desnecessários


class RevisaoForm(forms.ModelForm):
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = Revisao
        fields = ["numero_revisao", "data_revisao", "descricao_mudanca"]
        widgets = {
            "numero_revisao": forms.TextInput(attrs={"class": "form-control"}),
            "data_revisao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            # 'descricao_mudanca': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_numero_revisao(self):
        numero_revisao = self.cleaned_data.get("numero_revisao", "")
        return numero_revisao.title()

    def clean_descricao_mudanca(self):
        descricao_mudanca = self.cleaned_data.get("descricao_mudanca", "")
        return descricao_mudanca.strip()  # Apenas para remover espaços extras
