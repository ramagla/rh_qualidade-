# Generated by Django 5.1.2 on 2024-12-13 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0093_alter_historicocargo_data_atualizacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="cargo",
            name="educacao_minima",
            field=models.TextField(
                blank=True, null=True, verbose_name="Educação mínima"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="experiencia_minima",
            field=models.TextField(
                blank=True, null=True, verbose_name="Experiência mínima"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="responsabilidade_atividade_primaria",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Responsabilidade e Autoridade: (Atividade Primária)",
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="responsabilidade_atividade_secundaria",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Responsabilidade e Autoridade: (Atividade Secundária)",
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="treinamento_externo",
            field=models.TextField(
                blank=True, null=True, verbose_name="Treinamento / Curso (Externo)"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="treinamento_interno_minimo",
            field=models.TextField(
                blank=True, null=True, verbose_name="Treinamento mínimo (interno)"
            ),
        ),
    ]
