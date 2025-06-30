from django import forms
from django_select2.forms import Select2Widget
from django.contrib.auth.models import User

from rh_qualidade.utils import title_case

from ..models import Cargo, Funcionario
from ..models.departamentos import Departamentos
import datetime

class FuncionarioForm(forms.ModelForm):
    """
    Formulário completo para cadastro e edição de funcionários.
    Usa Select2, widgets customizados, validações de datas e regras específicas de segurança do trabalho.
    """

    ESCOLARIDADE_CHOICES = [("", "Selecione uma opção")] + sorted(
        [
            ("Fundamental Incompleto", "Fundamental Incompleto"),
            ("Fundamental Completo", "Fundamental Completo"),
            ("Médio Incompleto", "Médio Incompleto"),
            ("Médio Completo", "Médio Completo"),
            ("Superior Incompleto", "Superior Incompleto"),
            ("Superior Completo", "Superior Completo"),
            ("Técnico", "Técnico"),
            ("Pós-graduação", "Pós-graduação"),
            ("Mestrado", "Mestrado"),
            ("Doutorado", "Doutorado"),
        ],
        key=lambda x: x[1],
    )

    local_trabalho = forms.ModelChoiceField(
        queryset=Departamentos.objects.filter(ativo=True).order_by("nome"),
        label="Local de Trabalho",
        widget=Select2Widget(attrs={"class": "form-select select2"}),
        required=False,
    )

    cargo_inicial = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        label="Cargo Inicial",
        widget=Select2Widget(attrs={"class": "select2 form-select", "id": "id_cargo_inicial"}),
    )

    numero_registro_recibo = forms.CharField(
        required=False,
        label="Número do Registro para Recibo",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    cargo_atual = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        label="Cargo Atual",
        widget=Select2Widget(attrs={"class": "select2 form-select", "id": "id_cargo_atual"}),
    )

    data_admissao = forms.DateField(
        label="Data de Admissão",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )

    data_nascimento = forms.DateField(
        label="Data de Nascimento",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )

    escolaridade = forms.ChoiceField(
        choices=ESCOLARIDADE_CHOICES,
        label="Escolaridade",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    responsavel = forms.ModelChoiceField(
        queryset=Funcionario.objects.filter(status="Ativo").order_by("nome"),
        required=False,
        empty_label="Selecione um responsável",
        widget=Select2Widget(attrs={"class": "select2 form-select", "id": "id_responsavel"}),
        label="Responsável",
    )

    foto = forms.ImageField(required=False, label="Foto")
    assinatura_eletronica = forms.ImageField(required=False, label="Assinatura Eletrônica")
    curriculo = forms.FileField(required=False, label="Currículo")

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(funcionario__isnull=True).order_by("username"),
        required=False,
        label="Usuário do Sistema",
        widget=Select2Widget(attrs={"class": "select2 form-select", "data-placeholder": "Selecione um usuário"}),
    )

    status = forms.ChoiceField(
        choices=Funcionario.STATUS_CHOICES,
        label="Status",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    formulario_f146 = forms.FileField(required=False, label="Formulário F146")

    experiencia_profissional = forms.ChoiceField(
        choices=Funcionario.EXPERIENCIA_CHOICES,
        label="Experiência Profissional",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    camisa = forms.ChoiceField(
        choices=Funcionario.TAMANHO_CAMISA_CHOICES,
        label="Tamanho da Camisa",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    representante_cipa = forms.BooleanField(label="Representante CIPA", required=False)
    tipo_cipa = forms.ChoiceField(
        choices=[("", "---------"), ("Titular", "Titular"), ("Suplente", "Suplente")],
        required=False,
        label="Tipo CIPA",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    tipo_representacao_cipa = forms.ChoiceField(
        choices=[("", "---------"), ("Empregados", "Empregados"), ("Empregador", "Empregador")],
        required=False,
        label="Representa",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    vigencia_cipa = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        label="Vigência CIPA"
    )

    representante_brigada = forms.BooleanField(label="Representante Brigada", required=False)
    vigencia_brigada = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        label="Vigência Brigada"
    )

    ordem_cipa = forms.ChoiceField(
        label="Ordem na CIPA",
        choices=[("", "---------"), (1, "1º"), (2, "2º"), (3, "3º"), (4, "4º")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    data_desligamento = forms.DateField(
        label="Data de Desligamento",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )

    genero = forms.ChoiceField(
        choices=Funcionario.GENERO_CHOICES,
        label="Gênero",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    tipo = forms.ChoiceField(
        choices=Funcionario.TIPO_CHOICES,
        label="Tipo do Colaborador",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    calcado = forms.IntegerField(
        label="Número do Calçado",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Funcionario
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)

        # Ordenar os campos que dependem de consultas
        self.fields["cargo_inicial"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["cargo_atual"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["responsavel"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")

        if self.instance and self.instance.user:
            self.fields["user"].queryset = User.objects.filter(
                funcionario__isnull=True
            ) | User.objects.filter(pk=self.instance.user.pk)
        else:
            self.fields["user"].queryset = User.objects.filter(funcionario__isnull=True)

        if self.instance and self.instance.local_trabalho:
            self.fields["local_trabalho"].initial = self.instance.local_trabalho

        # Pré-carregar datas no formato ISO (YYYY-MM-DD)
        if self.instance and getattr(self.instance, "data_admissao", None):
            self.initial["data_admissao"] = self.instance.data_admissao.strftime("%Y-%m-%d")
        if self.instance and getattr(self.instance, "data_integracao", None):
            self.initial["data_integracao"] = self.instance.data_integracao.strftime("%Y-%m-%d")
        if self.instance and getattr(self.instance, "data_nascimento", None):
            self.initial["data_nascimento"] = self.instance.data_nascimento.strftime("%Y-%m-%d")

        # Adicionar classe "form-control" nos campos, exceto Select2Widget
        for name, field in self.fields.items():
            if not isinstance(field.widget, Select2Widget):
                field.widget.attrs.update({"class": "form-control"})

        self.fields["responsavel"].widget.attrs.update(
            {
                "class": "select2 form-select",
                "placeholder": "Selecione um responsável",
                "data-allow-clear": "true",
            }
        )

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome:
            return title_case(nome)
        return nome

    def clean(self):
        cleaned_data = super().clean()

        # Representante Brigada
        representante_brigada = cleaned_data.get("representante_brigada")
        vigencia_brigada = cleaned_data.get("vigencia_brigada")
        if representante_brigada and not vigencia_brigada:
            self.add_error("vigencia_brigada", "Informe a vigência da brigada para marcar o representante.")
        if vigencia_brigada and vigencia_brigada < datetime.date.today():
            cleaned_data["representante_brigada"] = False

        # Representante CIPA
        representante_cipa = cleaned_data.get("representante_cipa")
        vigencia_cipa = cleaned_data.get("vigencia_cipa")
        if representante_cipa and not vigencia_cipa:
            self.add_error("vigencia_cipa", "Informe a vigência da CIPA para marcar o representante.")
        if vigencia_cipa and vigencia_cipa < datetime.date.today():
            cleaned_data["representante_cipa"] = False

        # Validação de datas
        data_admissao = cleaned_data.get("data_admissao")
        data_desligamento = cleaned_data.get("data_desligamento")
        if data_admissao and data_desligamento and data_desligamento < data_admissao:
            self.add_error("data_desligamento", "A data de desligamento não pode ser anterior à data de admissão.")

        data_nascimento = cleaned_data.get("data_nascimento")
        if data_nascimento and data_nascimento > datetime.date.today():
            self.add_error("data_nascimento", "A data de nascimento não pode ser no futuro.")

        return cleaned_data

    def clean_ordem_cipa(self):
        ordem = self.cleaned_data.get("ordem_cipa")
        if ordem in ("", None):
            return None
        return ordem

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Preencher o cargo_responsavel com base no campo responsavel selecionado
        if instance.responsavel:
            instance.cargo_responsavel = instance.responsavel.cargo_atual

        # Forçar status para Inativo se data de desligamento estiver preenchida
        if instance.data_desligamento:
            instance.status = "Inativo"

        if commit:
            instance.save()
        return instance
