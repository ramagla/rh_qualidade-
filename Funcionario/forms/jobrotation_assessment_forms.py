# Funcionario/forms/jobrotation_assessment_forms.py
from django import forms
from ..models.jobrotation_assessments import (
    JobRotationAvaliacaoColaborador,
    JobRotationAvaliacaoGestor,
)
from ..models.job_rotation_evaluation import JobRotationEvaluation

class AvaliacaoColaboradorForm(forms.ModelForm):
    class Meta:
        model = JobRotationAvaliacaoColaborador
        exclude = (
            "token_publico",
            "assinado", "assinado_em", "assinado_ip", "assinado_hash",
            "assinante_nome", "assinante_email",
            "created", "updated",
        )
        widgets = {
            # cabeçalho
            "colaborador_nome": forms.TextInput(attrs={"class": "form-control"}),
            "cargo_anterior":   forms.TextInput(attrs={"class": "form-control"}),
            "cargo_atual":      forms.TextInput(attrs={"class": "form-control"}),
            "setor_anterior":   forms.TextInput(attrs={"class": "form-control"}),
            "setor_atual":      forms.TextInput(attrs={"class": "form-control"}),

            # selects
            "p1_infos_foram":   forms.Select(attrs={"class": "form-select"}),
            "p2_adaptacao":     forms.Select(attrs={"class": "form-select"}),
            "p3_desempenho":    forms.Select(attrs={"class": "form-select"}),
            "p4_atitude_duvida":forms.Select(attrs={"class": "form-select"}),
            "p5_metodo_empresa_ou_proprio": forms.Select(attrs={"class": "form-select"}),

            # textos longos
            "p1_favor_detalhar": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p2_detalhes":       forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p4_como_e_atendido":forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p5_justifique":     forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p6_detalhar":       forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p7_adaptou_facil":  forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p7_adaptou_dificil":forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p8_motivo_insatisfacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p9_como_adm_pessoal_ajuda": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "p10_critica_sugestao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class AvaliacaoGestorForm(forms.ModelForm):
    class Meta:
        model = JobRotationAvaliacaoGestor
        exclude = (
            "token_publico",
            "assinado", "assinado_em", "assinado_ip", "assinado_hash",
            "assinante_nome", "assinante_email",
            "created", "updated",
        )
        widgets = {
            "gestor_nome":  forms.TextInput(attrs={"class": "form-control"}),
            "gestor_cargo": forms.TextInput(attrs={"class": "form-control"}),
            "gestor_setor": forms.TextInput(attrs={"class": "form-control"}),

            "g1_infos_foram":       forms.Select(attrs={"class": "form-select"}),
            "g2_adaptacao":         forms.Select(attrs={"class": "form-select"}),
            "g3_desempenho":        forms.Select(attrs={"class": "form-select"}),
            "g4_atitude_duvida":    forms.Select(attrs={"class": "form-select"}),
            "g5_cooperacao":        forms.Select(attrs={"class": "form-select"}),

            "g1_de_quem":           forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "g1_detalhar":          forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g2_detalhar":          forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g4_como_e_atendido":   forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g5_justifique":        forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g6_detalhar":          forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g7_adaptou_facil":     forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g7_adaptou_dificil":   forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g8_motivo_insatisfacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g9_como_adm_pessoal_ajuda": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "g10_critica_sugestao":  forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class SelecionarJobRotationForm(forms.Form):
    jobrotation = forms.ModelChoiceField(
        label="Avaliação referente a",
        queryset=JobRotationEvaluation.objects.all().order_by("-data_inicio"),
        widget=forms.Select(attrs={"class": "form-select select2"}),
        required=True,
    )
