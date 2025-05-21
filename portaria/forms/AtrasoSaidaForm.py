from django import forms
from portaria.models import AtrasoSaida
from django.utils.timezone import localtime


from django.utils.timezone import localtime

class AtrasoSaidaForm(forms.ModelForm):
    class Meta:
        model = AtrasoSaida
        fields = ["funcionario", "data", "horario", "tipo", "observacao"]
        widgets = {
            "data": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            agora = localtime()
            self.fields["data"].initial = agora.date()
            self.fields["horario"].initial = agora.strftime("%H:%M")

        self.fields["funcionario"].widget.attrs.update({
            "class": "form-select select2",
            "id": "id_funcionario"
        })

