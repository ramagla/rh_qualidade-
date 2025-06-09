from django import forms
from comercial.models import Cliente

from django.forms import modelformset_factory

from comercial.models.clientes import ClienteDocumento

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

class ClienteDocumentoForm(forms.ModelForm):
    class Meta:
        model = ClienteDocumento
        fields = ['tipo', 'arquivo']

ClienteDocumentoFormSet = modelformset_factory(
    ClienteDocumento,
    form=ClienteDocumentoForm,
    extra=2,  # Quantos "novos documentos" exibir inicialmente
    can_delete=True
)
