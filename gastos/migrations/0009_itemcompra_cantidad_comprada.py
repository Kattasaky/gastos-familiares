from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gastos', '0008_alter_ingreso_es_fijo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcompra',
            name='cantidad_comprada',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
