from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from rh_qualidade.utils import title_case

from ..models import (
    AvaliacaoAnual,
    AvaliacaoExperiencia,
    AvaliacaoTreinamento,
    Funcionario,
    ListaPresenca,
    Treinamento,
)


class AvaliacaoForm(forms.ModelForm):
    descricao_melhorias = forms.CharField(
        widget=CKEditor5Widget(),
        required=True,
        label="Descreva as melhorias obtidas/resultados",
    )

    class Meta:
        model = AvaliacaoTreinamento
        fields = "__all__"


class AvaliacaoTreinamentoForm(forms.ModelForm):
    treinamento = (
        forms.ModelChoiceField(
            queryset=Treinamento.objects.all(),
            widget=forms.Select(attrs={"class": "form-select"}),
            label="Treinamento/Curso",
            required=True,
        ),
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
        widget=forms.HiddenInput(),  # Mude para IntegerField
        required=False,  # Ajuste se este campo não for obrigatório no formulário
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
            "anexo": forms.ClearableFileInput(attrs={"class": "form-control"}),

        }

    def __init__(self, *args, **kwargs):
        super(AvaliacaoTreinamentoForm, self).__init__(*args, **kwargs)

        # ✅ Corrigido: usa o modelo correto (Treinamento)
        self.fields["treinamento"].queryset = Treinamento.objects.all()
        self.fields["treinamento"].label = "Treinamento/Curso"

        # ✅ Responsáveis (somente funcionários ativos)
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



class AvaliacaoExperienciaForm(forms.ModelForm):
    observacoes = forms.CharField(
        widget=CKEditor5Widget(config_name="default"),  # Usando o CKEditor5Widget
        required=False,
        label="Observações",
    )

    class Meta:
        model = AvaliacaoExperiencia
        fields = "__all__"
        widgets = {
            "data_avaliacao": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"}
            ),
            "adaptacao_trabalho": forms.Select(
                choices=[
                    (
                        1,
                        "Ruim (D) - Mantém um comportamento oposto ao solicitado para seu cargo e demonstra dificuldades de aceitação.",
                    ),
                    (
                        2,
                        "Regular (C) - Precisa de muito esforço para se integrar ao trabalho e aos requisitos da Bras-Mol.",
                    ),
                    (
                        3,
                        "Bom (B) - Faz o possível para integrar-se ao trabalho e às características da Bras-Mol.",
                    ),
                    (
                        4,
                        "Ótimo (A) - Identifica-se plenamente com as atividades do cargo e normas da Bras-Mol.",
                    ),
                ],
                attrs={"class": "form-select"},
            ),
            "interesse": forms.Select(
                choices=[
                    (
                        1,
                        "Ruim (D) - Apresenta falta de entusiasmo e vontade de trabalhar.",
                    ),
                    (
                        2,
                        "Regular (C) - Necessitará de estímulo constante para se interessar pelo trabalho.",
                    ),
                    (
                        3,
                        "Bom (B) - Apresenta entusiasmo adequado para o tempo na Bras-Mol.",
                    ),
                    (4, "Ótimo (A) - Demonstra vivo interesse pelo novo trabalho."),
                ],
                attrs={"class": "form-select"},
            ),
            "relacionamento_social": forms.Select(
                choices=[
                    (
                        1,
                        "Ruim (D) - Sente-se perdido entre os colegas e parece não ter sido aceito.",
                    ),
                    (
                        2,
                        "Regular (C) - Esforça-se para conseguir maior integração social com os colegas.",
                    ),
                    (3, "Bom (B) - Entrosou-se bem e foi aceito sem resistência."),
                    (
                        4,
                        "Ótimo (A) - Demonstra grande habilidade em fazer amigos, sendo muito apreciado.",
                    ),
                ],
                attrs={"class": "form-select"},
            ),
            "capacidade_aprendizagem": forms.Select(
                choices=[
                    (1, "Ruim (D) - Parece não ter capacidade mínima para o trabalho."),
                    (
                        2,
                        "Regular (C) - Necessita de muito esforço e repetição para compreender as tarefas.",
                    ),
                    (3, "Bom (B) - Aprende suas tarefas sem dificuldades."),
                    (4, "Ótimo (A) - Habilitado para o cargo, executa sem falhas."),
                ],
                attrs={"class": "form-select"},
            ),
            "orientacao": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "gerencia": forms.TextInput(attrs={"class": "form-control"}),
            "avaliador": forms.Select(attrs={"class": "form-select"}),
            "avaliado": forms.Select(attrs={"class": "form-select"}),
            "funcionario": forms.Select(attrs={"class": "form-select select2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar funcionários ativos e ordenar por nome
        self.fields["funcionario"].queryset = Funcionario.objects.filter(
            status="Ativo"
        ).order_by("nome")


class AvaliacaoAnualForm(forms.ModelForm):
    avaliacao_global_avaliador = forms.CharField(
        widget=CKEditor5Widget(config_name="default"),
        required=False,
    )
    avaliacao_global_avaliado = forms.CharField(
        widget=CKEditor5Widget(config_name="default"),
        required=False,
    )

    class Meta:
        model = AvaliacaoAnual
        fields = "__all__"
        widgets = {
            "data_avaliacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔄 Filtrar funcionários ativos
        self.fields["funcionario"].queryset = Funcionario.objects.filter(
            status__iexact="Ativo"
        ).order_by("nome")

        # ✅ Campos do questionário como ChoiceField (1 a 4)
        escolhas = [
            (1, "Ruim"),
            (2, "Regular"),
            (3, "Bom"),
            (4, "Ótimo"),
        ]
        campos_questionario = [
            "postura_seg_trabalho",
            "qualidade_produtividade",
            "trabalho_em_equipe",
            "comprometimento",
            "disponibilidade_para_mudancas",
            "disciplina",
            "rendimento_sob_pressao",
            "proatividade",
            "comunicacao",
            "assiduidade",
        ]
        for campo in campos_questionario:
            self.fields[campo] = forms.ChoiceField(
                choices=[("", "---------")] + escolhas,
                widget=forms.Select(attrs={"class": "form-select item-avaliado"}),
                required=False,
                label=self.fields[campo].label if campo in self.fields else campo.replace("_", " ").capitalize(),
            )

    def clean_centro_custo(self):
        centro_custo = self.cleaned_data.get("centro_custo")
        if centro_custo:
            return title_case(centro_custo)
        return centro_custo