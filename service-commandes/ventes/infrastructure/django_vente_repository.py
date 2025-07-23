"""
Implémentation Django du VenteRepository
Infrastructure layer - convertit entre entités domain et modèles Django
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from ..application.repositories.vente_repository import VenteRepository
from ..domain.entities import Vente
from ..domain.value_objects import StatutVente, LigneVenteVO
from ..models import (
    Vente as VenteDjango,
    LigneVente as LigneVenteDjango,
    Magasin as MagasinDjango,
)


class DjangoVenteRepository(VenteRepository):
    """
    Implémentation concrète du VenteRepository utilisant Django ORM
    Responsabilité: Conversion entités domain <-> modèles Django
    """

    def save(self, vente: Vente) -> None:
        """Persiste une vente en base via Django ORM"""
        try:
            # Calcul du total de la vente
            total = vente.calculer_total()

            # Récupération ou création du modèle Django
            vente_django, created = VenteDjango.objects.get_or_create(
                id=vente.id,
                defaults={
                    "magasin_id": vente.magasin_id,
                    "client_id": vente.client_id,
                    "date_vente": vente.date_vente,
                    "total": total,
                    "statut": vente.statut.value,
                    "date_annulation": vente.date_annulation,
                    "motif_annulation": vente.motif_annulation,
                },
            )

            # Mise à jour si existant
            if not created:
                vente_django.total = total
                vente_django.statut = vente.statut.value
                vente_django.date_annulation = vente.date_annulation
                vente_django.motif_annulation = vente.motif_annulation
                vente_django.save()

            # Gestion des lignes de vente
            self._save_lignes_vente(vente_django, vente.lignes)

        except Exception as e:
            raise RuntimeError(f"Erreur lors de la persistance de la vente: {e}")

    def get_by_id(self, vente_id: str) -> Optional[Vente]:
        """Récupère une vente par son ID et la convertit en entité domain"""
        try:
            vente_django = VenteDjango.objects.prefetch_related("lignes").get(
                id=vente_id
            )
            return self._to_domain_entity(vente_django)
        except VenteDjango.DoesNotExist:
            return None

    def get_all(self) -> List[Vente]:
        """Récupère toutes les ventes et les convertit en entités domain"""
        ventes_django = VenteDjango.objects.prefetch_related("lignes").all()
        return [self._to_domain_entity(vente) for vente in ventes_django]

    def get_ventes_actives_by_magasin(self, magasin_id: UUID) -> List[Vente]:
        """Récupère les ventes actives d'un magasin"""
        ventes_django = VenteDjango.objects.prefetch_related("lignes").filter(
            magasin_id=magasin_id, statut=StatutVente.ACTIVE.value
        )
        return [self._to_domain_entity(vente) for vente in ventes_django]

    def get_ventes_actives_by_magasin_and_period(
        self, magasin_id: UUID, debut: datetime, fin: datetime
    ) -> List[Vente]:
        """Récupère les ventes actives d'un magasin sur une période"""
        ventes_django = VenteDjango.objects.prefetch_related("lignes").filter(
            magasin_id=magasin_id,
            statut=StatutVente.ACTIVE.value,
            date_vente__range=(debut, fin),
        )
        return [self._to_domain_entity(vente) for vente in ventes_django]

    def delete(self, vente_id: str) -> None:
        """Supprime une vente"""
        VenteDjango.objects.filter(id=vente_id).delete()

    def _to_domain_entity(self, vente_django: VenteDjango) -> Vente:
        """Convertit un modèle Django en entité domain"""
        # Création de l'entité avec les paramètres acceptés par le constructeur
        vente = Vente(
            id=vente_django.id,
            magasin_id=vente_django.magasin_id,
            client_id=vente_django.client_id,
            date_vente=vente_django.date_vente,
        )

        # Reconstitution de l'état interne (accès direct aux attributs privés)
        vente._statut = StatutVente(vente_django.statut)
        vente._date_annulation = vente_django.date_annulation
        vente._motif_annulation = vente_django.motif_annulation

        # Reconstitution des lignes de vente
        for ligne_django in vente_django.lignes.all():
            ligne_vo = LigneVenteVO(
                id=ligne_django.id,
                produit_id=ligne_django.produit_id,
                quantite=ligne_django.quantite,
                prix_unitaire=ligne_django.prix_unitaire,
            )
            vente._lignes.append(ligne_vo)  # Accès direct pour la reconstitution

        return vente

    def _save_lignes_vente(
        self, vente_django: VenteDjango, lignes: List[LigneVenteVO]
    ) -> None:
        """Persiste les lignes de vente"""
        # Suppression des anciennes lignes
        vente_django.lignes.all().delete()

        # Création des nouvelles lignes
        for ligne in lignes:
            LigneVenteDjango.objects.create(
                vente=vente_django,
                produit_id=ligne.produit_id,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
            )
