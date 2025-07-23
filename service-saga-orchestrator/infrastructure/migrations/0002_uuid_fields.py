# Migration pour corriger les types UUID

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sagamodel',
            name='magasin_id',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='sagamodel',
            name='commande_finale_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ] 