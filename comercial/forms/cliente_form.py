from django import forms
from django.forms import modelformset_factory
from comercial.models import Cliente
from comercial.models.clientes import ClienteDocumento

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campos_obrigatorios = [
            "razao_social", "cnpj", "endereco", "numero",
            "bairro", "cidade", "cep", "uf",
            "status", "tipo_cliente", "tipo_cadastro"
        ]

        for field_name in self.fields:
            field = self.fields[field_name]
            if field_name in campos_obrigatorios:
                field.required = True
                field.widget.attrs["required"] = "required"
                field.widget.attrs["class"] = field.widget.attrs.get("class", "") + " campo-obrigatorio"
            else:
                field.required = False

            if field.widget.__class__.__name__ == 'Select':
                field.widget.attrs["class"] = field.widget.attrs.get("class", "") + " form-select select2"

        # Filtra apenas clientes do tipo "Transportadora" no campo transportadora
        if "transportadora" in self.fields:
            self.fields["transportadora"].queryset = Cliente.objects.filter(tipo_cadastro="Transportadora")
            self.fields["transportadora"].widget.attrs["class"] = self.fields["transportadora"].widget.attrs.get("class", "") + " form-select select2"

class ClienteDocumentoForm(forms.ModelForm):
    class Meta:
        model = ClienteDocumento
        fields = ['tipo', 'arquivo']

ClienteDocumentoFormSet = modelformset_factory(
    ClienteDocumento,
    form=ClienteDocumentoForm,
    extra=2,
    can_delete=True
)
