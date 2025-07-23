# Generated migration for Saga Orchestrator

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SagaModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('client_id', models.UUIDField()),
                ('magasin_id', models.CharField(max_length=50)),
                ('etat_actuel', models.CharField(choices=[('EN_ATTENTE', 'EN_ATTENTE'), ('VERIFICATION_STOCK', 'VERIFICATION_STOCK'), ('STOCK_VERIFIE', 'STOCK_VERIFIE'), ('RESERVATION_STOCK', 'RESERVATION_STOCK'), ('STOCK_RESERVE', 'STOCK_RESERVE'), ('CREATION_COMMANDE', 'CREATION_COMMANDE'), ('COMMANDE_CREEE', 'COMMANDE_CREEE'), ('SAGA_TERMINEE', 'SAGA_TERMINEE'), ('ECHEC_STOCK_INSUFFISANT', 'ECHEC_STOCK_INSUFFISANT'), ('ECHEC_RESERVATION_STOCK', 'ECHEC_RESERVATION_STOCK'), ('ECHEC_CREATION_COMMANDE', 'ECHEC_CREATION_COMMANDE'), ('COMPENSATION_EN_COURS', 'COMPENSATION_EN_COURS'), ('SAGA_ANNULEE', 'SAGA_ANNULEE')], default='EN_ATTENTE', max_length=50)),
                ('donnees_contexte', models.JSONField(default=dict)),
                ('reservation_stock_ids', models.JSONField(default=dict)),
                ('commande_finale_id', models.CharField(blank=True, max_length=100, null=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('est_terminee', models.BooleanField(default=False)),
                ('necessite_compensation', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Saga Commande',
                'verbose_name_plural': 'Saga Commandes',
                'db_table': 'saga_commandes',
                'ordering': ['-date_creation'],
            },
        ),
        migrations.CreateModel(
            name='LigneCommandeModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('produit_id', models.CharField(max_length=100)),
                ('quantite', models.PositiveIntegerField()),
                ('saga', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes_commande', to='infrastructure.sagamodel')),
            ],
            options={
                'verbose_name': 'Ligne Commande Saga',
                'verbose_name_plural': 'Lignes Commande Saga',
                'db_table': 'saga_lignes_commande',
            },
        ),
        migrations.CreateModel(
            name='EvenementSagaModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_evenement', models.CharField(choices=[('SAGA_DEMARRE', 'SAGA_DEMARRE'), ('STOCK_VERIFIE_SUCCES', 'STOCK_VERIFIE_SUCCES'), ('STOCK_VERIFIE_ECHEC', 'STOCK_VERIFIE_ECHEC'), ('STOCK_RESERVE_SUCCES', 'STOCK_RESERVE_SUCCES'), ('STOCK_RESERVE_ECHEC', 'STOCK_RESERVE_ECHEC'), ('COMMANDE_CREEE_SUCCES', 'COMMANDE_CREEE_SUCCES'), ('COMMANDE_CREEE_ECHEC', 'COMMANDE_CREEE_ECHEC'), ('COMPENSATION_DEMANDEE', 'COMPENSATION_DEMANDEE'), ('COMPENSATION_TERMINEE', 'COMPENSATION_TERMINEE'), ('SAGA_TERMINEE_SUCCES', 'SAGA_TERMINEE_SUCCES'), ('SAGA_TERMINEE_ECHEC', 'SAGA_TERMINEE_ECHEC')], max_length=50)),
                ('etat_precedent', models.CharField(blank=True, choices=[('EN_ATTENTE', 'EN_ATTENTE'), ('VERIFICATION_STOCK', 'VERIFICATION_STOCK'), ('STOCK_VERIFIE', 'STOCK_VERIFIE'), ('RESERVATION_STOCK', 'RESERVATION_STOCK'), ('STOCK_RESERVE', 'STOCK_RESERVE'), ('CREATION_COMMANDE', 'CREATION_COMMANDE'), ('COMMANDE_CREEE', 'COMMANDE_CREEE'), ('SAGA_TERMINEE', 'SAGA_TERMINEE'), ('ECHEC_STOCK_INSUFFISANT', 'ECHEC_STOCK_INSUFFISANT'), ('ECHEC_RESERVATION_STOCK', 'ECHEC_RESERVATION_STOCK'), ('ECHEC_CREATION_COMMANDE', 'ECHEC_CREATION_COMMANDE'), ('COMPENSATION_EN_COURS', 'COMPENSATION_EN_COURS'), ('SAGA_ANNULEE', 'SAGA_ANNULEE')], max_length=50, null=True)),
                ('nouvel_etat', models.CharField(choices=[('EN_ATTENTE', 'EN_ATTENTE'), ('VERIFICATION_STOCK', 'VERIFICATION_STOCK'), ('STOCK_VERIFIE', 'STOCK_VERIFIE'), ('RESERVATION_STOCK', 'RESERVATION_STOCK'), ('STOCK_RESERVE', 'STOCK_RESERVE'), ('CREATION_COMMANDE', 'CREATION_COMMANDE'), ('COMMANDE_CREEE', 'COMMANDE_CREEE'), ('SAGA_TERMINEE', 'SAGA_TERMINEE'), ('ECHEC_STOCK_INSUFFISANT', 'ECHEC_STOCK_INSUFFISANT'), ('ECHEC_RESERVATION_STOCK', 'ECHEC_RESERVATION_STOCK'), ('ECHEC_CREATION_COMMANDE', 'ECHEC_CREATION_COMMANDE'), ('COMPENSATION_EN_COURS', 'COMPENSATION_EN_COURS'), ('SAGA_ANNULEE', 'SAGA_ANNULEE')], max_length=50)),
                ('message', models.TextField(blank=True)),
                ('donnees', models.JSONField(default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('saga', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evenements', to='infrastructure.sagamodel')),
            ],
            options={
                'verbose_name': 'Événement Saga',
                'verbose_name_plural': 'Événements Saga',
                'db_table': 'saga_evenements',
                'ordering': ['timestamp'],
            },
        ),
    ] 