"""
Implémentation Django du repository pour les commandes e-commerce
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from ..application.repositories.commande_ecommerce_repository import (
    CommandeEcommerceRepository,
)
from ..domain.entities import CommandeEcommerce as CommandeEcommerceDomain
from ..domain.value_objects import LigneCommande, AdresseLivraison
from ..models import (
    CommandeEcommerce as CommandeEcommerceDjango,
    LigneCommandeEcommerce as LigneCommandeEcommerceDjango,
)


class DjangoCommandeEcommerceRepository(CommandeEcommerceRepository):
    """
    Implémentation concrète du repository utilisant Django ORM
    """

    def save(self, commande: CommandeEcommerceDomain) -> CommandeEcommerceDomain:
        """Sauvegarde une commande e-commerce"""
        try:
            # Convertir l'entité domaine vers le modèle Django
            django_commande, created = CommandeEcommerceDjango.objects.get_or_create(
                id=commande.id,
                defaults={
                    "client_id": commande.client_id,
                    "checkout_id": commande.checkout_id,
                    "statut": commande.statut,
                    "date_commande": commande.date_commande,
                    "sous_total": commande.sous_total,
                    "frais_livraison": commande.frais_livraison,
                    "total": commande.total,
                    "nom_destinataire": (
                        commande.adresse_livraison.nom_destinataire
                        if commande.adresse_livraison
                        else ""
                    ),
                    "rue": (
                        commande.adresse_livraison.rue
                        if commande.adresse_livraison
                        else ""
                    ),
                    "ville": (
                        commande.adresse_livraison.ville
                        if commande.adresse_livraison
                        else ""
                    ),
                    "code_postal": (
                        commande.adresse_livraison.code_postal
                        if commande.adresse_livraison
                        else ""
                    ),
                    "province": (
                        commande.adresse_livraison.province
                        if commande.adresse_livraison
                        else ""
                    ),
                    "pays": (
                        commande.adresse_livraison.pays
                        if commande.adresse_livraison
                        else "Canada"
                    ),
                    "instructions_livraison": (
                        commande.adresse_livraison.instructions_livraison
                        if commande.adresse_livraison
                        else None
                    ),
                    "livraison_express": (
                        commande.adresse_livraison.livraison_express
                        if commande.adresse_livraison
                        else False
                    ),
                    "notes": commande.notes,
                    "nombre_articles": commande.nombre_articles,
                    "nombre_produits": commande.nombre_produits,
                },
            )

            # Mise à jour si pas nouvelle
            if not created:
                django_commande.statut = commande.statut
                django_commande.sous_total = commande.sous_total
                django_commande.frais_livraison = commande.frais_livraison
                django_commande.total = commande.total
                django_commande.notes = commande.notes
                django_commande.nombre_articles = commande.nombre_articles
                django_commande.nombre_produits = commande.nombre_produits
                django_commande.save()

            # Sauvegarder les lignes de commande
            self._save_lignes_commande(django_commande, commande.lignes)

            return self._mapper_vers_domaine(django_commande)

        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde de la commande: {str(e)}")

    def get_by_id(self, commande_id: UUID) -> Optional[CommandeEcommerceDomain]:
        """Récupère une commande par son ID"""
        try:
            django_commande = CommandeEcommerceDjango.objects.get(id=commande_id)
            return self._mapper_vers_domaine(django_commande)
        except CommandeEcommerceDjango.DoesNotExist:
            return None

    def get_by_client_id(
        self, client_id: UUID, limit: int = 50
    ) -> List[CommandeEcommerceDomain]:
        """Récupère toutes les commandes d'un client"""
        django_commandes = CommandeEcommerceDjango.objects.filter(
            client_id=client_id
        ).order_by("-date_commande")[:limit]

        return [self._mapper_vers_domaine(cmd) for cmd in django_commandes]

    def get_by_checkout_id(
        self, checkout_id: UUID
    ) -> Optional[CommandeEcommerceDomain]:
        """Récupère une commande par son checkout ID"""
        try:
            django_commande = CommandeEcommerceDjango.objects.get(
                checkout_id=checkout_id
            )
            return self._mapper_vers_domaine(django_commande)
        except CommandeEcommerceDjango.DoesNotExist:
            return None

    def get_recent_commandes(
        self, days: int = 30, limit: int = 100
    ) -> List[CommandeEcommerceDomain]:
        """Récupère les commandes récentes"""
        date_limite = datetime.now() - timedelta(days=days)

        django_commandes = CommandeEcommerceDjango.objects.filter(
            date_commande__gte=date_limite
        ).order_by("-date_commande")[:limit]

        return [self._mapper_vers_domaine(cmd) for cmd in django_commandes]

    def _save_lignes_commande(
        self, django_commande: CommandeEcommerceDjango, lignes: List[LigneCommande]
    ) -> None:
        """Sauvegarde les lignes de commande"""
        # Supprimer les anciennes lignes
        LigneCommandeEcommerceDjango.objects.filter(commande=django_commande).delete()

        # Créer les nouvelles lignes
        for ligne in lignes:
            LigneCommandeEcommerceDjango.objects.create(
                commande=django_commande,
                produit_id=ligne.produit_id,
                nom_produit=ligne.nom_produit,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
                prix_total=ligne.prix_total(),
            )

    def _mapper_vers_domaine(
        self, django_commande: CommandeEcommerceDjango
    ) -> CommandeEcommerceDomain:
        """Convertit un modèle Django vers une entité domaine"""
        # Créer l'entité domaine
        commande_domaine = CommandeEcommerceDomain(
            id=django_commande.id,
            client_id=django_commande.client_id,
            checkout_id=django_commande.checkout_id,
            statut=django_commande.statut,
            date_commande=django_commande.date_commande,
        )

        # Définir les détails financiers
        commande_domaine.definir_details_financiers(
            sous_total=django_commande.sous_total,
            frais_livraison=django_commande.frais_livraison,
        )

        # Définir l'adresse de livraison
        if django_commande.nom_destinataire:
            adresse = AdresseLivraison(
                nom_destinataire=django_commande.nom_destinataire,
                rue=django_commande.rue,
                ville=django_commande.ville,
                code_postal=django_commande.code_postal,
                province=django_commande.province,
                pays=django_commande.pays,
                instructions_livraison=django_commande.instructions_livraison,
                livraison_express=django_commande.livraison_express,
            )
            commande_domaine.definir_adresse_livraison(adresse)

        # Ajouter les lignes de commande
        for ligne_django in django_commande.lignes.all():
            ligne_domaine = LigneCommande(
                produit_id=ligne_django.produit_id,
                nom_produit=ligne_django.nom_produit,
                quantite=ligne_django.quantite,
                prix_unitaire=ligne_django.prix_unitaire,
            )
            commande_domaine.ajouter_ligne(ligne_domaine)

        # Définir les notes
        if django_commande.notes:
            commande_domaine.definir_notes(django_commande.notes)

        return commande_domaine
