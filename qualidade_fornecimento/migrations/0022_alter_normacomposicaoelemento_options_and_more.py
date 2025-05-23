# Generated by Django 4.2.16 on 2025-04-10 13:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0021_normatecnica_tipo_abnt"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="normacomposicaoelemento",
            options={
                "verbose_name": "Composição Química (por tipo ABNT)",
                "verbose_name_plural": "Composições Químicas",
            },
        ),
        migrations.AlterModelOptions(
            name="normatecnica",
            options={
                "verbose_name": "Norma Técnica",
                "verbose_name_plural": "Normas Técnicas",
            },
        ),
        migrations.AlterModelOptions(
            name="normatracao",
            options={
                "verbose_name": "Faixa de Tração",
                "verbose_name_plural": "Faixas de Tração",
            },
        ),
        migrations.RemoveField(
            model_name="normacomposicaoelemento",
            name="elemento",
        ),
        migrations.RemoveField(
            model_name="normacomposicaoelemento",
            name="maximo",
        ),
        migrations.RemoveField(
            model_name="normacomposicaoelemento",
            name="minimo",
        ),
        migrations.RemoveField(
            model_name="normatecnica",
            name="tipo_abnt",
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="al_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Al máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="al_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Al mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="c_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="C máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="c_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="C mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="cr_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Cr máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="cr_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Cr mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="cu_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Cu máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="cu_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Cu mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="mn_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Mn máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="mn_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Mn mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="ni_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Ni máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="ni_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Ni mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="p_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="P máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="p_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="P mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="s_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="S máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="s_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="S mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="si_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Si máx (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="si_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                verbose_name="Si mín (%)",
            ),
        ),
        migrations.AddField(
            model_name="normacomposicaoelemento",
            name="tipo_abnt",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Tipo de Aço ABNT"
            ),
        ),
        migrations.AlterField(
            model_name="normatecnica",
            name="arquivo_norma",
            field=models.FileField(upload_to="normas/", verbose_name="Arquivo (PDF)"),
        ),
        migrations.AlterField(
            model_name="normatecnica",
            name="nome_norma",
            field=models.CharField(max_length=100, verbose_name="Nome da Norma"),
        ),
        migrations.AlterField(
            model_name="normatecnica",
            name="vinculo_norma",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="relacionadas",
                to="qualidade_fornecimento.normatecnica",
                verbose_name="Norma vinculada (tração)",
            ),
        ),
        migrations.AlterField(
            model_name="normatracao",
            name="bitola_maxima",
            field=models.DecimalField(
                decimal_places=2, max_digits=6, verbose_name="Bitola máx (mm)"
            ),
        ),
        migrations.AlterField(
            model_name="normatracao",
            name="bitola_minima",
            field=models.DecimalField(
                decimal_places=2, max_digits=6, verbose_name="Bitola mín (mm)"
            ),
        ),
        migrations.AlterField(
            model_name="normatracao",
            name="resistencia_max",
            field=models.DecimalField(
                decimal_places=2, max_digits=8, verbose_name="R. tração máx (Kgf/mm²)"
            ),
        ),
        migrations.AlterField(
            model_name="normatracao",
            name="resistencia_min",
            field=models.DecimalField(
                decimal_places=2, max_digits=8, verbose_name="R. tração mín (Kgf/mm²)"
            ),
        ),
    ]
