from django import forms
from django_select2.forms import Select2Widget

from rh_qualidade.utils import title_case

from ..models import Cargo, Funcionario


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

    local_trabalho = forms.ChoiceField(
        choices=[("", "Selecione uma opção")]
        + [
            (dep, dep)
            for dep in Cargo.objects.values_list("departamento", flat=True)
            .distinct()
            .order_by("departamento")
        ],
        label="Local de Trabalho",
        widget=forms.Select(attrs={"class": "form-select select2"}),
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
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data de Admissão",
    )
    data_integracao = forms.DateField(
        required=False,  # Torna o campo opcional
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data de Integração",
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
    )  # Novo campo
    curriculo = forms.FileField(required=False, label="Currículo")
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

        widgets = {
            "local_trabalho": Select2Widget(
                attrs={
                    "class": "select2 form-select",
                    "placeholder": "Selecione um local de trabalho",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)

        # Ordenar os campos que dependem de consultas
        self.fields["cargo_inicial"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["cargo_atual"].queryset = Cargo.objects.all().order_by("nome")
        self.fields["responsavel"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")

        # Preenche o local_trabalho com o valor da instância
        if self.instance and self.instance.local_trabalho:
            self.fields["local_trabalho"].initial = self.instance.local_trabalho

        # Adicionar classe "form-control" nos campos, exceto Select2Widget
        for field in self.fields:
            if not isinstance(self.fields[field].widget, Select2Widget):
                self.fields[field].widget.attrs.update({"class": "form-control"})

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
        local_trabalho = self.cleaned_data.get("local_trabalho")
        if local_trabalho:
            # Aplica a função title_case personalizada
            return title_case(local_trabalho)
        return local_trabalho

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
