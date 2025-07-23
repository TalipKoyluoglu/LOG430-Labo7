"""
Repository Django pour la persistance des Sagas
Implémentation concrete pour sauvegarder l'état des sagas en base de données
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid

from django.db import models
from django.utils import timezone

from domain.entities import SagaCommande, EtatSaga, TypeEvenement, LigneCommande, EvenementSaga


class SagaModel(models.Model):
    """Modèle Django pour persister une Saga"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.UUIDField()
    magasin_id = models.UUIDField()  # UUID du magasin pour cohérence microservices
    
    # État actuel de la saga
    etat_actuel = models.CharField(
        max_length=50,
        choices=[(e.value, e.value) for e in EtatSaga],
        default=EtatSaga.EN_ATTENTE.value
    )
    
    # Données contextuelles (JSON)
    donnees_contexte = models.JSONField(default=dict)
    
    # IDs des réservations stock (JSON)
    reservation_stock_ids = models.JSONField(default=dict)
    
    # ID de la commande finale créée (UUID)
    commande_finale_id = models.UUIDField(null=True, blank=True)
    
    # Timestamps
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    
    # Statut
    est_terminee = models.BooleanField(default=False)
    necessite_compensation = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'saga_commandes'
        verbose_name = 'Saga Commande'
        verbose_name_plural = 'Saga Commandes'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Saga {self.id} - {self.etat_actuel}"


class LigneCommandeModel(models.Model):
    """Modèle Django pour les lignes de commande d'une saga"""
    
    saga = models.ForeignKey(SagaModel, on_delete=models.CASCADE, related_name='lignes_commande')
    produit_id = models.CharField(max_length=100)
    quantite = models.PositiveIntegerField()
    
    class Meta:
        db_table = 'saga_lignes_commande'
        verbose_name = 'Ligne Commande Saga'
        verbose_name_plural = 'Lignes Commande Saga'
    
    def __str__(self):
        return f"Ligne {self.produit_id} x{self.quantite}"


class EvenementSagaModel(models.Model):
    """Modèle Django pour l'historique des événements d'une saga"""
    
    saga = models.ForeignKey(SagaModel, on_delete=models.CASCADE, related_name='evenements')
    
    # Type d'événement
    type_evenement = models.CharField(
        max_length=50,
        choices=[(e.value, e.value) for e in TypeEvenement]
    )
    
    # États
    etat_precedent = models.CharField(
        max_length=50,
        choices=[(e.value, e.value) for e in EtatSaga],
        null=True, blank=True
    )
    nouvel_etat = models.CharField(
        max_length=50,
        choices=[(e.value, e.value) for e in EtatSaga]
    )
    
    # Métadonnées
    message = models.TextField(blank=True)
    donnees = models.JSONField(default=dict)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saga_evenements'
        verbose_name = 'Événement Saga'
        verbose_name_plural = 'Événements Saga'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Événement {self.type_evenement} - {self.nouvel_etat}"


class DjangoSagaRepository:
    """
    Repository concret utilisant Django ORM pour persister les sagas
    """
    
    def save(self, saga: SagaCommande) -> SagaCommande:
        """Sauvegarde une saga et ses données associées"""
        
        # Créer ou mettre à jour le modèle principal
        saga_model, created = SagaModel.objects.get_or_create(
            id=saga.id,
            defaults={
                'client_id': saga.client_id,
                'magasin_id': saga.magasin_id,
                'etat_actuel': saga.etat_actuel.value,
                'donnees_contexte': saga.donnees_contexte,
                'reservation_stock_ids': saga.reservation_stock_ids,
                'commande_finale_id': saga.commande_finale_id,
                'est_terminee': bool(saga.est_terminee),
                'necessite_compensation': bool(saga.necessite_compensation),
            }
        )
        
        if not created:
            # Mettre à jour si existe déjà
            saga_model.etat_actuel = saga.etat_actuel.value
            saga_model.donnees_contexte = saga.donnees_contexte
            saga_model.reservation_stock_ids = saga.reservation_stock_ids
            saga_model.commande_finale_id = saga.commande_finale_id
            saga_model.est_terminee = bool(saga.est_terminee)
            saga_model.necessite_compensation = bool(saga.necessite_compensation)
            
            if saga.est_terminee and not saga_model.date_fin:
                saga_model.date_fin = timezone.now()
            
            saga_model.save()
        
        # Sauvegarder les lignes de commande si nécessaire
        if created:
            for ligne in saga.lignes_commande:
                LigneCommandeModel.objects.create(
                    saga=saga_model,
                    produit_id=ligne.produit_id,
                    quantite=ligne.quantite
                )
        
        # Sauvegarder les nouveaux événements
        evenements_existants = EvenementSagaModel.objects.filter(saga=saga_model).count()
        nouveaux_evenements = saga.evenements[evenements_existants:]
        
        for evenement in nouveaux_evenements:
            EvenementSagaModel.objects.create(
                saga=saga_model,
                type_evenement=evenement.type_evenement.value,
                etat_precedent=evenement.etat_precedent.value if evenement.etat_precedent else None,
                nouvel_etat=evenement.nouvel_etat.value,
                message=evenement.message,
                donnees=evenement.donnees or {}
            )
        
        return saga
    
    def get_by_id(self, saga_id: str) -> Optional[SagaCommande]:
        """Récupère une saga par son ID"""
        try:
            saga_model = SagaModel.objects.get(id=saga_id)
            return self._to_domain_entity(saga_model)
        except SagaModel.DoesNotExist:
            return None
    
    def get_all_actives(self) -> List[SagaCommande]:
        """Récupère toutes les sagas actives (non terminées)"""
        saga_models = SagaModel.objects.filter(est_terminee=False)
        return [self._to_domain_entity(model) for model in saga_models]
    
    def get_all(self) -> List[SagaCommande]:
        """Récupère toutes les sagas (terminées et non terminées)"""
        saga_models = SagaModel.objects.all().order_by('-date_creation')
        return [self._to_domain_entity(model) for model in saga_models]
    
    def get_by_etat(self, etat: EtatSaga) -> List[SagaCommande]:
        """Récupère toutes les sagas dans un état donné"""
        saga_models = SagaModel.objects.filter(etat_actuel=etat.value)
        return [self._to_domain_entity(model) for model in saga_models]
    
    def _to_domain_entity(self, saga_model: SagaModel) -> SagaCommande:
        """Convertit un modèle Django en entité du domaine"""
        
        # Récupérer les lignes de commande
        lignes_models = saga_model.lignes_commande.all()
        lignes_commande = [
            LigneCommande(
                produit_id=ligne.produit_id,
                quantite=ligne.quantite,
                prix_unitaire=0.0,  # Sera récupéré du catalogue lors de l'exécution
                nom_produit=""       # Sera récupéré du catalogue lors de l'exécution
            )
            for ligne in lignes_models
        ]
        
        # Récupérer les événements
        evenements_models = saga_model.evenements.all()
        evenements = [
            EvenementSaga(
                type_evenement=TypeEvenement(evt.type_evenement),
                etat_precedent=EtatSaga(evt.etat_precedent) if evt.etat_precedent else None,
                nouvel_etat=EtatSaga(evt.nouvel_etat),
                message=evt.message,
                donnees=evt.donnees,
                timestamp=evt.timestamp
            )
            for evt in evenements_models
        ]
        
        # Créer l'entité saga
        saga = SagaCommande(
            id=saga_model.id,
            client_id=saga_model.client_id,
            magasin_id=saga_model.magasin_id,
            lignes_commande=lignes_commande
        )
        
        # Restaurer l'état
        saga.etat_actuel = EtatSaga(saga_model.etat_actuel)
        saga.donnees_contexte = saga_model.donnees_contexte
        saga.reservation_stock_ids = saga_model.reservation_stock_ids
        saga.commande_finale_id = saga_model.commande_finale_id
        saga.evenements = evenements
        
        return saga 