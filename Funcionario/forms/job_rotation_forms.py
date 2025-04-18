from datetime import timedelta

from django import forms
from django.utils import timezone
from django_ckeditor_5.widgets import CKEditor5Widget

from ..models import AvaliacaoAnual, JobRotationEvaluation


class JobRotationEvaluationForm(forms.ModelForm):
    treinamentos_requeridos = forms.CharField(widget=CKEditor5Widget(), required=False)
    treinamentos_propostos = forms.CharField(widget=CKEditor5Widget(), required=False)
    avaliacao_gestor = forms.CharField(widget=CKEditor5Widget(), required=False)
    avaliacao_funcionario = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = JobRotationEvaluation
        fields = "__all__"

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get("data_inicio")
        limite_retroativo = timezone.now().date() - timedelta(
            days=365
        )  # Permite até 1 ano no passado
        if data_inicio and data_inicio < limite_retroativo:
            raise forms.ValidationError(
                "A data de início não pode ser retroativa além de 1 ano."
            )
        return data_inicio

    def clean_area_atual(self):
        """Garante que o campo 'Área Atual' esteja em Title Case."""
        area_atual = self.cleaned_data.get("area_atual")
        if area_atual:
            return area_atual.title()  # Converte para Title Case
        return area_atual

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Preencher campos automaticamente baseado no funcionário selecionado
        if instance.funcionario:
            # Atribui o cargo atual e a área atual do funcionário
            instance.cargo_atual = instance.funcionario.cargo_atual
            # A área atual é o 'local_trabalho' de Funcionario
            instance.area_atual = instance.funcionario.local_trabalho
            instance.escolaridade = (
                instance.funcionario.escolaridade
            )  # Atribui escolaridade

            # Calcular o término previsto (adiciona 60 dias à data de início)
            if instance.data_inicio:
                instance.termino_previsto = instance.data_inicio + timedelta(days=60)

            # Preenche a última avaliação, se necessário
            try:
                ultima_avaliacao = instance.funcionario.avaliacaoanual_set.latest(
                    "data_avaliacao"
                )
                instance.data_ultima_avaliacao = ultima_avaliacao.data_avaliacao
                classificacao = ultima_avaliacao.calcular_classificacao()
                instance.status_ultima_avaliacao = classificacao["status"]
            except AvaliacaoAnual.DoesNotExist:
                instance.data_ultima_avaliacao = (
                    None  # Se não houver avaliação, deixe como None
                )
                instance.status_ultima_avaliacao = (
                    "Indeterminado"  # Ou outro status default
                )

            # Preenche a descrição do cargo, se disponível
            if instance.funcionario.cargo_atual:
                # Atribui descrição do cargo
                instance.descricao_cargo = (
                    instance.funcionario.cargo_atual.descricao_arquivo
                )

            # Preenche a lista de cursos realizados, caso haja
            cursos = instance.funcionario.treinamentos.filter(
                status="concluido"
            )  # Apenas cursos concluídos
            # Cria uma lista com os nomes dos cursos
            cursos_realizados = [curso.nome_curso for curso in cursos]
            instance.cursos_realizados = (
                cursos_realizados  # Atribui à lista de cursos realizados
            )

        if commit:
            instance.save()
        return instance
