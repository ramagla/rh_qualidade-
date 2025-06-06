# Generated by Django 4.2.16 on 2025-04-10 11:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0017_remove_normacomposicaoquimica_materia_prima"),
    ]

    operations = [
        migrations.AddField(
            model_name="normacomposicaoquimica",
            name="vinculo_norma",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="relacionadas",
                to="qualidade_fornecimento.normacomposicaoquimica",
                verbose_name="Vínculo da Norma (Tração)",
            ),
        ),
    ]
