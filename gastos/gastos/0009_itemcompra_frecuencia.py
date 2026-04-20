from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gastos', '0008_alter_ingreso_es_fijo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcompra',
            name='frecuencia',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('semanal', 'Semanal'),
                    ('quincenal', 'Quincenal'),
                    ('mensual', 'Mensual'),
                    ('unica', 'Única vez'),
                ],
                default='mensual',
            ),
        ),
    ]
