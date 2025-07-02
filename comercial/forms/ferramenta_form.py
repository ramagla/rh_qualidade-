from django import forms
from django.forms import inlineformset_factory
from comercial.models import Ferramenta, MaoDeObraFerramenta, ServicoFerramenta
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

            # Novos campos técnicos
            "passo": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "largura_tira": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "num_matrizes": forms.NumberInput(attrs={"class": "form-control"}),
            "num_puncoes": forms.NumberInput(attrs={"class": "form-control"}),
            "num_carros": forms.NumberInput(attrs={"class": "form-control"}),
            "num_formadores": forms.NumberInput(attrs={"class": "form-control"}),
            "bloco": forms.Select(attrs={"class": "form-select select2"}),

        }


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


from django import forms
from django.forms import inlineformset_factory
from comercial.models.ferramenta import BlocoFerramenta, ItemBloco

class BlocoForm(forms.ModelForm):
    class Meta:
        model = BlocoFerramenta
        fields = ["numero"]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Bloco 1"})
        }

class ItemBlocoForm(forms.ModelForm):
    class Meta:
        model = ItemBloco
        exclude = ("bloco",)
        widgets = {
            "numero_item": forms.TextInput(attrs={"class": "form-control"}),
            "medidas": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 25,4x94x165"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "peso_aco": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

ItemBlocoFormSet = inlineformset_factory(
    BlocoFerramenta,
    ItemBloco,
    form=ItemBlocoForm,
    extra=1,
    can_delete=True
)
