from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from comercial.models import Ferramenta, MaoDeObraFerramenta, ServicoFerramenta
from django_ckeditor_5.widgets import CKEditor5Widget
from decimal import Decimal, InvalidOperation

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
            "valor_unitario_sae": forms.NumberInput(attrs={"class": "form-control"}),
            "valor_unitario_vnd": forms.NumberInput(attrs={"class": "form-control"}),

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
        # Remova ou corrija essa linha. Se estiver tentando adicionar um formulário a mais, use extra no formset.
        # Exemplo correto de incremento no momento da definição do formset:
        # ItemBlocoFormSet = modelformset_factory(ItemBloco, form=ItemBlocoForm, extra=1, can_delete=True)


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

# 🧱 Formulário do Bloco
class BlocoForm(forms.ModelForm):
    class Meta:
        model = BlocoFerramenta
        fields = ["numero"]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Bloco 1"})
        }


# 🧩 Formulário dos Itens do Bloco
# 🧩 Formulário dos Itens do Bloco
class ItemBlocoForm(forms.ModelForm):
    volume = forms.DecimalField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control js-volume',
            'readonly': 'readonly'
        })
    )

    peso_total = forms.DecimalField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control js-peso-total',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = ItemBloco
        exclude = ("bloco", "volume", "peso_total")
        widgets = {
            "numero_item": forms.TextInput(attrs={"class": "form-control"}),
            "medidas": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 25,4x94x165"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "peso_aco": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Corrige vírgulas para ponto ANTES da validação
        if self.data:
            self.data = self.data.copy()
            for name in self.fields:
                if "volume" in name or "peso_total" in name:
                    key = self.add_prefix(name)
                    if key in self.data:
                        self.data[key] = self.data[key].replace(",", ".")




# 🧠 Formset base personalizado: injeta 7 linhas somente no cadastro
class ItemBlocoBaseFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        # Informa que vamos tratar o número total de formulários manualmente
        super().__init__(*args, **kwargs)

        # Só adiciona formulários extras se for cadastro (sem itens ainda)
        if not self.instance.pk and self.total_form_count() < 7:
            extras_necessarios = 7 - self.total_form_count()
            for i in range(extras_necessarios):
                 self.forms.append(self._construct_form(self.total_form_count() + i))





# 🧾 Inline Formset
ItemBlocoFormSet = inlineformset_factory(
    BlocoFerramenta,
    ItemBloco,
    form=ItemBlocoForm,
    formset=ItemBlocoBaseFormSet,  # Usa a classe customizada
    extra=0,
    can_delete=True
)

