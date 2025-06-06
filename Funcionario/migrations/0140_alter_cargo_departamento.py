# Generated by Django 4.2.16 on 2025-05-28 19:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0139_alter_funcionario_local_trabalho"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cargo",
            name="departamento",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cargos",
                to="Funcionario.departamentos",
                verbose_name="Departamento",
            ),
        ),
    ]
