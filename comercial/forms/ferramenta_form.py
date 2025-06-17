from django import forms
from django.forms import inlineformset_factory
from comercial.models import Ferramenta, MaterialFerramenta, MaoDeObraFerramenta, ServicoFerramenta
from django_ckeditor_5.widgets import CKEditor5Widget

# 🛠️ Formulário principal de ferramenta
class FerramentaForm(forms.ModelForm):
    class Meta:
        model = Ferramenta
        fields = '__all__'
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 255,
                "placeholder": "Descrição resumida"
            }),
            "vida_util_em_pecas": forms.NumberInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select select2"}),
            "proprietario": forms.Select(attrs={"class": "form-select select2"}),
            "desenho_pdf": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "observacoes": CKEditor5Widget(config_name="default"),
        }

# 🧱 Formulário de materiais da ferramenta
class MaterialFerramentaForm(forms.ModelForm):
    class Meta:
        model = MaterialFerramenta
        exclude = ('ferramenta',)
        widgets = {
            "nome_material": forms.TextInput(attrs={"class": "form-control"}),
            "unidade_medida": forms.Select(attrs={"class": "form-select"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control"}),
            "valor_unitario": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_unitario'].required = False

MaterialFerramentaFormSet = inlineformset_factory(
    Ferramenta,
    MaterialFerramenta,
    form=MaterialFerramentaForm,
    extra=1,
    can_delete=True
)


# 👷 Formulário de mão de obra
class MaoDeObraFerramentaForm(forms.ModelForm):
    class Meta:
        model = MaoDeObraFerramenta
        exclude = ('ferramenta',)
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "horas": forms.NumberInput(attrs={"class": "form-control"}),
            "valor_hora": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_hora'].required = False

MaoDeObraFormSet = inlineformset_factory(
    Ferramenta,
    MaoDeObraFerramenta,
    form=MaoDeObraFerramentaForm,
    extra=1,
    can_delete=True
)


# 🔧 Formulário de serviços terceiros
class ServicoFerramentaForm(forms.ModelForm):
    class Meta:
        model = ServicoFerramenta
        exclude = ('ferramenta',)
        widgets = {
            "tipo_servico": forms.Select(attrs={"class": "form-select"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control"}),
            "valor_unitario": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_unitario'].required = False

ServicoFormSet = inlineformset_factory(
    Ferramenta,
    ServicoFerramenta,
    form=ServicoFerramentaForm,
    extra=1,
    can_delete=True
)

