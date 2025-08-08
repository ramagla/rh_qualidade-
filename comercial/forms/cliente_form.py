from django import forms
from django.forms import modelformset_factory
from comercial.models import Cliente
from comercial.models.clientes import ClienteDocumento

from django import forms
from comercial.models import Cliente

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

        # 🔃 Filtra apenas clientes do tipo "Transportadora"
        if "transportadora" in self.fields:
            self.fields["transportadora"].queryset = Cliente.objects.filter(tipo_cadastro="Transportadora")
            self.fields["transportadora"].widget.attrs["class"] = self.fields["transportadora"].widget.attrs.get("class", "") + " form-select select2"

        # 🧷 Remove o comportamento do ClearableFileInput (que adiciona "atualmente... limpar")
        if "comprovante_adimplencia" in self.fields:
            self.fields["comprovante_adimplencia"].widget = forms.FileInput(attrs={"class": "form-control"})

    def clean_comprovante_adimplencia(self):
        file = self.cleaned_data.get("comprovante_adimplencia")
        if file and not file.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Apenas arquivos PDF são permitidos.")
        return file

from django.core.files.uploadedfile import UploadedFile
    
class ClienteDocumentoForm(forms.ModelForm):
    class Meta:
        model = ClienteDocumento
        fields = ['tipo', 'arquivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].widget.attrs.update({'class': 'form-select'})
        # agora usa FileInput simples, sem checkbox “Limpar”
        self.fields['arquivo'].widget = forms.FileInput(
            attrs={'class': 'form-control'}
        )

    def clean_arquivo(self):
        file = self.cleaned_data.get('arquivo')
        if not file:
            return None

        # Se for um FieldFile (arquivo já existente), pula validação de tipo/tamanho
        if not isinstance(file, UploadedFile):
            return file

        # 1) Tipos permitidos (só para uploads novos)
        content_type = file.content_type
        allowed_types = [
            'application/pdf',
            'image/jpeg', 'image/png', 'image/gif',
        ]
        if content_type not in allowed_types:
            raise forms.ValidationError(
                "Formato inválido. Envie PDF ou imagem (JPEG, PNG, GIF)."
            )

        # 2) Tamanho máximo 5 MB
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            raise forms.ValidationError(
                "Arquivo muito grande. Tamanho máximo: 5 MB."
            )

        return file


ClienteDocumentoFormSet = modelformset_factory(
    ClienteDocumento,
    form=ClienteDocumentoForm,
    extra=0,
    can_delete=True
)
