from django.db import models

class ComposicaoQuimica(models.Model):
    norma = models.CharField(max_length=100)
    classe = models.CharField(max_length=100)
    codigo_norma = models.CharField(max_length=200, editable=False)

    carbono_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    carbono_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    manganes_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    manganes_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    silicio_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    silicio_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    fosforo_min = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    fosforo_max = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)

    enxofre_min = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    enxofre_max = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)

    cromo_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    cromo_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    niquel_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    niquel_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    cobre_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    cobre_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    aluminio_min = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    aluminio_max = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.codigo_norma = f"{self.norma}-{self.classe}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo_norma
