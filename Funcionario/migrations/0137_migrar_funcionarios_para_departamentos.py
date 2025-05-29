from django.db import migrations

def migrar_funcionarios_para_fk(apps, schema_editor):
    Funcionario = apps.get_model("Funcionario", "Funcionario")
    Departamentos = apps.get_model("Funcionario", "Departamentos")

    for funcionario in Funcionario.objects.all():
        if isinstance(funcionario.local_trabalho, str):
            try:
                dep = Departamentos.objects.get(sigla=funcionario.local_trabalho)
                funcionario.local_trabalho = dep
                funcionario.save(update_fields=["local_trabalho"])
            except Departamentos.DoesNotExist:
                funcionario.local_trabalho = None
                funcionario.save(update_fields=["local_trabalho"])

class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0136_alter_funcionario_local_trabalho"),  # Ajuste conforme necessário
    ]

    operations = [
        migrations.RunPython(migrar_funcionarios_para_fk),
    ]







