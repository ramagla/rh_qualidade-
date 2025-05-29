from django import forms
from django_select2.forms import Select2Widget
from django.contrib.auth.models import User

from rh_qualidade.utils import title_case

from ..models import Cargo, Funcionario
from ..models.departamentos import Departamentos


class FuncionarioForm(forms.ModelForm):
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
        widget=Select2Widget(
            attrs={"class": "select2 form-select", "id": "id_cargo_inicial"}
        ),
    )
    cargo_atual = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        label="Cargo Atual",
        widget=Select2Widget(
            attrs={"class": "select2 form-select", "id": "id_cargo_atual"}
        ),
    )
    data_admissao = forms.DateField(
        label="Data de Admissão",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"}
        ),
        input_formats=["%Y-%m-%d"],
    )
    data_nascimento = forms.DateField(
        label="Data de Nascimento",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"}
        ),
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
        widget=Select2Widget(
            attrs={"class": "select2 form-select", "id": "id_responsavel"}
        ),
        label="Responsável",
    )
    foto = forms.ImageField(required=False, label="Foto")
    assinatura_eletronica = forms.ImageField(
        required=False, label="Assinatura Eletrônica"
    )    
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

    # Novo campo Experiência Profissional
    experiencia_profissional = forms.ChoiceField(
        choices=Funcionario.EXPERIENCIA_CHOICES,
        label="Experiência Profissional",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Funcionario
        fields = "__all__"  # Ou liste explicitamente os campos, incluindo 'status'

        

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)

        # Ordenar os campos que dependem de consultas
        self.fields["cargo_inicial"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["cargo_atual"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["responsavel"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")

        # ⬇️ Adiciona lógica para o campo user
        from django.contrib.auth.models import User
        if self.instance and self.instance.user:
            self.fields["user"].queryset = User.objects.filter(
                funcionario__isnull=True
            ) | User.objects.filter(pk=self.instance.user.pk)
        else:
            self.fields["user"].queryset = User.objects.filter(funcionario__isnull=True)

        # Preenche o local_trabalho com o valor da instância
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

        # Adicionar Select2 ao campo "responsavel"
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
            return title_case(nome)  # Aplica a função title_case personalizada
        return nome

    def clean_local_trabalho(self):
        return self.cleaned_data.get("local_trabalho")

    def clean_responsavel(self):
        responsavel = self.cleaned_data.get("responsavel", None)
        return responsavel  # Não altera mais o nome do responsável diretamente

        # Método save para preencher o cargo_responsavel automaticamente

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Preencher o cargo_responsavel com base no campo responsavel selecionado
        if instance.responsavel:
            # Certifique-se de que `cargo_atual` é uma instância válida de `Cargo`
            instance.cargo_responsavel = instance.responsavel.cargo_atual

        if commit:
            instance.save()
        return instance
