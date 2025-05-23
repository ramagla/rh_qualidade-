# Generated by Django 4.2.16 on 2025-05-20 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0111_alter_cargo_departamento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cargo",
            name="departamento",
            field=models.CharField(
                choices=[
                    ("RH", "Recursos Humanos"),
                    ("QUALIDADE", "Gestão da Qualidade"),
                    ("CONTROLE", "Controle de Qualidade"),
                    ("PRODUCAO", "Produção"),
                    ("COMPRAS", "Compras"),
                    ("COMERCIAL", "Comercial"),
                    ("DIRETORIA", "Diretoria"),
                    ("PCP", "Logistica/PCP"),
                    ("LIMPEZA", "Serviços Gerais"),
                    ("TÉCNICO", "Técnico"),
                    ("TI", "Técnologia da Informação"),
                    ("ALMOXARIFADO", "Almoxarifado"),
                    ("EXPEDICAO", "Expedição"),
                    ("MANUTENÇÃO", "Manutenção"),
                    ("COMPRESSAO", "Compressão"),
                    ("RETIFICA", "Retífica"),
                    ("TORSÃO", "Torção"),
                    ("ESTAMPARIA_BIHLER", "Estamparia Bihler"),
                    ("ACABAMENTO", "Acabamento"),
                    ("PRENSA", "Prensa"),
                    ("DOBRADEIRA_CNC", "Dobradeira CNC"),
                    ("ALIVIO_TENSAO_TECNICO", "Alívio de Tensão Técnico"),
                ],
                max_length=50,
                verbose_name="Departamento",
            ),
        ),
    ]
