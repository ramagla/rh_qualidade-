from django import forms
from django.db.models import Q
from django.utils.timezone import localtime
from portaria.models import AtrasoSaida
from Funcionario.models import Funcionario  # <- para filtrar status=Ativo

class AtrasoSaidaForm(forms.ModelForm):
    class Meta:
        model = AtrasoSaida
        fields = ["funcionario", "data", "horario", "hora_fim", "tipo", "observacao"]
        widgets = {
            "data": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Preenche data/horário padrão apenas na criação
        if not self.instance.pk:
            agora = localtime()
            self.fields["data"].initial = agora.date()
            self.fields["horario"].initial = agora.strftime("%H:%M")

        # 🔒 Mostrar somente funcionários ATIVOS.
        # Observação: ao editar um registro antigo cujo funcionário foi inativado,
        # mantemos esse funcionário no queryset para não quebrar o formulário.
        qs_ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")
        if self.instance.pk and getattr(self.instance, "funcionario_id", None):
            qs_ativos = qs_ativos | Funcionario.objects.filter(pk=self.instance.funcionario_id)

        self.fields["funcionario"].queryset = qs_ativos.distinct()

        # Mantém Select2 e id do campo
        self.fields["funcionario"].widget.attrs.update({
            "class": "form-select select2",
            "id": "id_funcionario",
        })
