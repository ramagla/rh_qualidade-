from django import forms
from django.core.exceptions import ValidationError
from ..models.jobrotation_assessments import (
    JobRotationAvaliacaoColaborador, JobRotationAvaliacaoGestor
)

class AvaliacaoColaboradorForm(forms.ModelForm):
    class Meta:
        model = JobRotationAvaliacaoColaborador
        exclude = ["token_publico","assinado","assinado_em","assinado_ip","assinado_hash",
                   "assinante_nome","assinante_email","created","updated"]
        widgets = {
            "p1_favor_detalhar": forms.Textarea(attrs={"rows":3}),
            "p2_detalhes": forms.Textarea(attrs={"rows":3}),
            "p4_como_e_atendido": forms.Textarea(attrs={"rows":3}),
            "p5_justifique": forms.Textarea(attrs={"rows":3}),
            "p6_detalhar": forms.Textarea(attrs={"rows":3}),
            "p7_adaptou_facil": forms.Textarea(attrs={"rows":3}),
            "p7_adaptou_dificil": forms.Textarea(attrs={"rows":3}),
            "p8_motivo_insatisfacao": forms.Textarea(attrs={"rows":3}),
            "p9_como_adm_pessoal_ajuda": forms.Textarea(attrs={"rows":3}),
            "p10_critica_sugestao": forms.Textarea(attrs={"rows":3}),
        }

    def clean(self):
        c = super().clean()
        # regras condicionais típicas
        if c.get("p1_recebeu_infos") and c.get("p1_infos_foram") == "insuficientes" and not c.get("p1_faltaram"):
            self.add_error("p1_faltaram", "Informe o tipo de informação que faltou.")
        if not c.get("p6_dialogo_com_chefe") and not c.get("p6_detalhar"):
            self.add_error("p6_detalhar", "Detalhe a ausência de diálogo.")
        if not c.get("p8_satisfeito") and not c.get("p8_motivo_insatisfacao"):
            self.add_error("p8_motivo_insatisfacao", "Explique o motivo de não estar satisfeito.")
        return c


class AvaliacaoGestorForm(forms.ModelForm):
    class Meta:
        model = JobRotationAvaliacaoGestor
        exclude = ["token_publico","assinado","assinado_em","assinado_ip","assinado_hash",
                   "assinante_nome","assinante_email","created","updated"]
        widgets = {
            "g1_de_quem": forms.Textarea(attrs={"rows":2}),
            "g1_detalhar": forms.Textarea(attrs={"rows":3}),
            "g2_detalhar": forms.Textarea(attrs={"rows":3}),
            "g4_como_e_atendido": forms.Textarea(attrs={"rows":3}),
            "g5_justifique": forms.Textarea(attrs={"rows":3}),
            "g6_detalhar": forms.Textarea(attrs={"rows":3}),
            "g7_adaptou_facil": forms.Textarea(attrs={"rows":3}),
            "g7_adaptou_dificil": forms.Textarea(attrs={"rows":3}),
            "g8_motivo_insatisfacao": forms.Textarea(attrs={"rows":3}),
            "g9_como_adm_pessoal_ajuda": forms.Textarea(attrs={"rows":3}),
            "g10_critica_sugestao": forms.Textarea(attrs={"rows":3}),
        }

    def clean(self):
        c = super().clean()
        if c.get("g1_func_tinha_info") and not c.get("g1_de_quem"):
            self.add_error("g1_de_quem", "Informe de quem vinham as informações.")
        if c.get("g1_infos_foram") == "insuficientes" and not c.get("g1_faltaram"):
            self.add_error("g1_faltaram", "Informe o tipo de informação que faltou.")
        if not c.get("g6_treinamento_dialogo") and not c.get("g6_detalhar"):
            self.add_error("g6_detalhar", "Detalhe a ausência de diálogo.")
        if not c.get("g8_satisfeito") and not c.get("g8_motivo_insatisfacao"):
            self.add_error("g8_motivo_insatisfacao", "Explique o motivo de não estar satisfeito.")
        return c
