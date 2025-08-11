from datetime import timedelta

from django import forms
from django.utils import timezone
from django_ckeditor_5.widgets import CKEditor5Widget

from ..models import AvaliacaoAnual, JobRotationEvaluation
from django.core.files.uploadedfile import UploadedFile


class JobRotationEvaluationForm(forms.ModelForm):
    """
    Formulário para avaliação de job rotation.
    Valida datas, converte área atual para Title Case e preenche diversos campos automaticamente no save.
    """
    treinamentos_requeridos = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=False
    )
    treinamentos_propostos = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=False
    )

    avaliacao_gestor = forms.CharField(widget=CKEditor5Widget(), required=False)
    avaliacao_funcionario = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = JobRotationEvaluation
        fields = "__all__"
        widgets = {"anexo": forms.FileInput(attrs={"class": "form-control","accept": ".pdf,.doc,.docx"}),}
                    
    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get("data_inicio")
        limite_retroativo = timezone.now().date() - timedelta(days=365)
        if data_inicio and data_inicio < limite_retroativo:
            raise forms.ValidationError(
                "A data de início não pode ser retroativa além de 1 ano."
            )
        return data_inicio

    def clean_area_atual(self):
        """Garante que o campo 'Área Atual' esteja em Title Case."""
        area_atual = self.cleaned_data.get("area_atual")
        if area_atual:
            return area_atual.title()
        return area_atual
    
    def clean_anexo(self):
        f = self.cleaned_data.get("anexo")
        if isinstance(f, UploadedFile) and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("O arquivo excede 5 MB.")
        return f

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.funcionario:
            # Atribui o cargo atual e a área atual do funcionário
            instance.cargo_atual = instance.funcionario.cargo_atual
            instance.area_atual = instance.funcionario.local_trabalho
            instance.escolaridade = instance.funcionario.escolaridade

            # Calcular o término previsto (60 dias após início)
            if instance.data_inicio:
                instance.termino_previsto = instance.data_inicio + timedelta(days=60)

            # Última avaliação anual
            try:
                ultima_avaliacao = instance.funcionario.avaliacaoanual_set.latest("data_avaliacao")
                instance.data_ultima_avaliacao = ultima_avaliacao.data_avaliacao
                classificacao = ultima_avaliacao.calcular_classificacao()
                instance.status_ultima_avaliacao = classificacao["status"]
            except AvaliacaoAnual.DoesNotExist:
                instance.data_ultima_avaliacao = None
                instance.status_ultima_avaliacao = "Indeterminado"

            # Descrição do cargo
            if instance.funcionario.cargo_atual:
                instance.descricao_cargo = instance.funcionario.cargo_atual.descricao_arquivo

            # Cursos realizados
            cursos = instance.funcionario.treinamentos.filter(status="concluido")
            cursos_realizados = [curso.nome_curso for curso in cursos]
            instance.cursos_realizados = cursos_realizados

            # Treinamentos da nova função
            if instance.nova_funcao:
                if not instance.treinamentos_requeridos:
                    instance.treinamentos_requeridos = instance.nova_funcao.treinamento_interno_minimo or ""
                if not instance.treinamentos_propostos:
                    instance.treinamentos_propostos = instance.nova_funcao.treinamento_externo or ""

        if commit:
            instance.save()
        return instance
