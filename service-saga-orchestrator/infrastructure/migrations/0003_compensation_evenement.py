# Migration pour ajouter COMPENSATION_DEMANDEE dans les choix des événements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0002_uuid_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evenementsagamodel',
            name='type_evenement',
            field=models.CharField(choices=[
                ('SAGA_DEMARRE', 'SAGA_DEMARRE'), 
                ('STOCK_VERIFIE_SUCCES', 'STOCK_VERIFIE_SUCCES'), 
                ('STOCK_VERIFIE_ECHEC', 'STOCK_VERIFIE_ECHEC'), 
                ('STOCK_RESERVE_SUCCES', 'STOCK_RESERVE_SUCCES'), 
                ('STOCK_RESERVE_ECHEC', 'STOCK_RESERVE_ECHEC'), 
                ('COMMANDE_CREEE_SUCCES', 'COMMANDE_CREEE_SUCCES'), 
                ('COMMANDE_CREEE_ECHEC', 'COMMANDE_CREEE_ECHEC'), 
                ('COMPENSATION_DEMANDEE', 'COMPENSATION_DEMANDEE'), 
                ('COMPENSATION_TERMINEE', 'COMPENSATION_TERMINEE'), 
                ('SAGA_TERMINEE_SUCCES', 'SAGA_TERMINEE_SUCCES')
            ], max_length=50),
        ),
    ] 