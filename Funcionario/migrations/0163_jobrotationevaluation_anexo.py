# Generated by Django 4.2.16 on 2025-07-02 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0162_fechamentoindicadortreinamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobrotationevaluation",
            name="anexo",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="job_rotation/evaluations/%Y/%m/%d/",
                verbose_name="Anexo (arquivo)",
            ),
        ),
    ]
