from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from Funcionario.models import Funcionario, Treinamento, AvaliacaoTreinamento


class AvaliacaoTreinamentoForm(forms.ModelForm):
    """
    Formulário para avaliação de treinamentos/cursos.
    Usa widgets customizados, radios para respostas e CKEditor para texto.
    Filtra responsáveis apenas para funcionários ativos.
    Garante que pelo menos um responsável seja informado.
    """
    treinamento = forms.ModelChoiceField(
        queryset=Treinamento.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Treinamento/Curso",
        required=True,
    )

    pergunta_1 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        widget=forms.RadioSelect,
        required=False,
        label="Grau de conhecimento atual dos participantes da metodologia",
    )
    pergunta_2 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_APLICACAO,
        widget=forms.RadioSelect,
        required=False,
        label="Aplicação dos conceitos da metodologia",
    )
    pergunta_3 = forms.ChoiceField(
        choices=AvaliacaoTreinamento.OPCOES_RESULTADOS,
        widget=forms.RadioSelect,
        required=False,
        label="Resultados obtidos com a aplicação da metodologia",
    )
    descricao_melhorias = forms.CharField(
        widget=CKEditor5Widget(),
        required=True,
        label="Descreva as melhorias obtidas/resultados",
    )
    avaliacao_geral = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = AvaliacaoTreinamento
        fields = "__all__"
        widgets = {
            "responsavel_1": forms.Select(attrs={"class": "form-select"}),
            "responsavel_2": forms.Select(attrs={"class": "form-select"}),
            "responsavel_3": forms.Select(attrs={"class": "form-select"}),
            "funcionario": forms.Select(attrs={"class": "form-select"}),
            "treinamento": forms.Select(attrs={"class": "form-select"}),
            "anexo": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar treinamentos e responsáveis apenas ativos
        self.fields["treinamento"].queryset = Treinamento.objects.all()
        self.fields["treinamento"].label = "Treinamento/Curso"

        ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")

        self.fields["responsavel_1"].queryset = ativos
        self.fields["responsavel_1"].required = False
        self.fields["responsavel_1"].label = "Primeiro Responsável (opcional)"

        self.fields["responsavel_2"].queryset = ativos
        self.fields["responsavel_2"].required = False
        self.fields["responsavel_2"].label = "Segundo Responsável (opcional)"

        self.fields["responsavel_3"].queryset = ativos
        self.fields["responsavel_3"].required = False
        self.fields["responsavel_3"].label = "Terceiro Responsável (opcional)"

    def clean(self):
        """
        Validação para garantir que pelo menos um responsável seja informado.
        """
        cleaned_data = super().clean()
        r1 = cleaned_data.get("responsavel_1")
        r2 = cleaned_data.get("responsavel_2")
        r3 = cleaned_data.get("responsavel_3")

        if not (r1 or r2 or r3):
            raise forms.ValidationError(
                "Pelo menos um responsável deve ser informado."
            )
        return cleaned_data
