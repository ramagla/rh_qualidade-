# portaria/forms/entrada_visitante_form.py
from django import forms
from portaria.models import EntradaVisitante, PessoaPortaria, VeiculoPortaria


class EntradaVisitanteForm(forms.ModelForm):
    TIPOS = [
        ("visitante", "Visitante"),
        ("entregador", "Entregador"),
    ]

    pessoa = forms.ModelChoiceField(
        queryset=PessoaPortaria.objects.none(),  # sobrescrito no init
        required=False,
        label="Pessoa já cadastrada",
        widget=forms.Select(attrs={"class": "form-select select2"})
    )

    nome = forms.CharField(required=False, label="Nome", widget=forms.TextInput(attrs={"class": "form-control"}))
    documento = forms.CharField(required=False, label="RG", widget=forms.TextInput(attrs={"class": "form-control"}))
    empresa = forms.CharField(required=False, label="Empresa", widget=forms.TextInput(attrs={"class": "form-control"}))
    foto = forms.ImageField(required=False, label="Foto")

    tipo = forms.ChoiceField(
        required=False,
        choices=TIPOS,
        label="Tipo",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    tipo_veiculo = forms.ChoiceField(
        required=False,
        choices=[
            ("carro", "Carro"),
            ("moto", "Moto"),
            ("caminhao", "Caminhão"),
            ("outro", "Outro")
        ],
        label="Tipo do Veículo",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = EntradaVisitante
        fields = [
            "pessoa", "nome", "documento", "empresa", "tipo", "foto",
            "veiculo", "data", "hora_entrada", "hora_saida",
            "falar_com", "motivo", "outro_motivo"
        ]
        widgets = {
            "data": forms.DateInput(
                format="%Y-%m-%d",

                 attrs={"type": "date", "class": "form-control"}),
            "hora_entrada": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "hora_saida": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "falar_com": forms.TextInput(attrs={"class": "form-control"}),
            "motivo": forms.Select(attrs={"class": "form-select"}),
            "outro_motivo": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pessoa"].queryset = PessoaPortaria.objects.filter(tipo__in=["visitante", "entregador"]).order_by("nome")

    def clean(self):
            cleaned_data = super().clean()
            pessoa = cleaned_data.get("pessoa")
            documento = cleaned_data.get("documento")
            veiculo_manual = self.data.get("veiculo_manual")  # ainda é string no POST

            if not pessoa:
                if documento and PessoaPortaria.objects.filter(documento=documento).exists():
                    raise forms.ValidationError("Já existe uma pessoa cadastrada com este RG.")
                
                if veiculo_manual and VeiculoPortaria.objects.filter(placa__iexact=veiculo_manual).exists():
                    raise forms.ValidationError("Já existe um veículo com esta placa cadastrado.")