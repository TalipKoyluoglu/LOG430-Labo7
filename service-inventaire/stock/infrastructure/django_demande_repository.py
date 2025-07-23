"""
Implémentation Django du repository Demande
Convertit entre les modèles Django et les entités DDD.
"""

from typing import List, Optional
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from ..models import DemandeReapprovisionnement as DjangoDemandeReapprovisionnement
from ..application.repositories.demande_repository import DemandeRepository
from ..domain.entities import DemandeReapprovisionnement, StatutDemandeStock
from ..domain.value_objects import DemandeId, ProduitId, MagasinId, Quantite


class DjangoDemandeRepository(DemandeRepository):
    """Implémentation concrète du repository Demande utilisant Django ORM"""

    def get_by_id(self, demande_id: DemandeId) -> Optional[DemandeReapprovisionnement]:
        """Récupère une demande par son identifiant"""
        try:
            django_demande = DjangoDemandeReapprovisionnement.objects.get(
                id=str(demande_id)
            )
            return self._mapper_vers_domaine(django_demande)
        except ObjectDoesNotExist:
            return None

    def get_demandes_by_statut(
        self, statut: StatutDemandeStock
    ) -> List[DemandeReapprovisionnement]:
        """Récupère toutes les demandes avec un statut spécifique"""
        django_demandes = DjangoDemandeReapprovisionnement.objects.filter(
            statut=statut.value
        )
        return [self._mapper_vers_domaine(demande) for demande in django_demandes]

    def get_demandes_en_attente(self) -> List[DemandeReapprovisionnement]:
        """Récupère toutes les demandes en attente de traitement"""
        django_demandes = DjangoDemandeReapprovisionnement.objects.filter(
            statut=StatutDemandeStock.EN_ATTENTE.value
        )
        return [self._mapper_vers_domaine(demande) for demande in django_demandes]

    def get_demandes_by_magasin(
        self, magasin_id: MagasinId
    ) -> List[DemandeReapprovisionnement]:
        """Récupère toutes les demandes d'un magasin spécifique"""
        django_demandes = DjangoDemandeReapprovisionnement.objects.filter(
            magasin_id=str(magasin_id)
        )
        return [self._mapper_vers_domaine(demande) for demande in django_demandes]

    def get_demandes_by_produit(
        self, produit_id: ProduitId
    ) -> List[DemandeReapprovisionnement]:
        """Récupère toutes les demandes pour un produit spécifique"""
        django_demandes = DjangoDemandeReapprovisionnement.objects.filter(
            produit_id=str(produit_id)
        )
        return [self._mapper_vers_domaine(demande) for demande in django_demandes]

    def save(self, demande: DemandeReapprovisionnement) -> DemandeReapprovisionnement:
        """Sauvegarde une demande (création ou mise à jour)"""
        try:
            # Tentative de mise à jour
            django_demande = DjangoDemandeReapprovisionnement.objects.get(
                id=str(demande.demande_id)
            )
            django_demande.quantite = int(demande.quantite)
            django_demande.statut = demande.statut.value
            if hasattr(demande, "date_modification") and demande.date_modification:
                # Mise à jour manuelle car le modèle Django n'a pas ce champ
                pass
            django_demande.save()
        except ObjectDoesNotExist:
            # Création
            django_demande = DjangoDemandeReapprovisionnement.objects.create(
                id=str(demande.demande_id),
                produit_id=str(demande.produit_id),
                magasin_id=str(demande.magasin_id),
                quantite=int(demande.quantite),
                statut=demande.statut.value,
                date=demande.date_creation,
            )

        return self._mapper_vers_domaine(django_demande)

    def delete(self, demande_id: DemandeId) -> bool:
        """Supprime une demande"""
        try:
            DjangoDemandeReapprovisionnement.objects.get(id=str(demande_id)).delete()
            return True
        except ObjectDoesNotExist:
            return False

    def exists_demande_en_attente(
        self, produit_id: ProduitId, magasin_id: MagasinId
    ) -> bool:
        """Vérifie s'il existe déjà une demande en attente pour ce produit/magasin"""
        return DjangoDemandeReapprovisionnement.objects.filter(
            produit_id=str(produit_id),
            magasin_id=str(magasin_id),
            statut=StatutDemandeStock.EN_ATTENTE.value,
        ).exists()

    # Méthodes de mapping

    def _mapper_vers_domaine(
        self, django_demande: DjangoDemandeReapprovisionnement
    ) -> DemandeReapprovisionnement:
        """Convertit un modèle Django DemandeReapprovisionnement vers une entité domaine"""
        return DemandeReapprovisionnement(
            demande_id=DemandeId(str(django_demande.id)),
            produit_id=ProduitId(str(django_demande.produit_id)),
            magasin_id=MagasinId(str(django_demande.magasin_id)),
            quantite=Quantite.from_int(django_demande.quantite),
            statut=StatutDemandeStock(django_demande.statut),
            date_creation=django_demande.date,
            date_modification=None,  # Le modèle Django actuel n'a pas ce champ
        )
