"""
Use Case: Lister les commandes d'un client
Permet de consulter l'historique des commandes e-commerce d'un client
"""

import uuid
import logging
from typing import Dict, Any, List

from ..repositories.commande_ecommerce_repository import CommandeEcommerceRepository
from ...domain.exceptions import ClientInvalideError

logger = logging.getLogger("commandes")


class ListerCommandesClientUseCase:
    """
    Use Case: Consulter l'historique des commandes e-commerce d'un client

    Récupère toutes les commandes passées par un client avec leurs détails
    """

    def __init__(self, commande_repository: CommandeEcommerceRepository):
        self._commande_repo = commande_repository

    def execute(self, client_id: str, limite: int = 50) -> Dict[str, Any]:
        """
        Récupère l'historique des commandes d'un client

        Args:
            client_id: UUID du client
            limite: Nombre maximum de commandes à retourner

        Returns:
            Dict contenant la liste des commandes et les statistiques
        """

        logger.debug(f"Récupération historique commandes pour client {client_id}")

        try:
            # Validation de l'UUID client
            client_uuid = uuid.UUID(client_id)
        except ValueError:
            raise ClientInvalideError(f"UUID client invalide: {client_id}")

        # Récupération des commandes
        commandes_domaine = self._commande_repo.get_by_client_id(client_uuid, limite)

        if not commandes_domaine:
            logger.debug(f"Aucune commande trouvée pour client {client_id}")
            return {
                "client_id": client_id,
                "commandes": [],
                "statistiques": {
                    "nombre_commandes": 0,
                    "total_depense": 0.0,
                    "commande_moyenne": 0.0,
                    "derniere_commande": None,
                },
            }

        # Formatage des commandes pour l'API
        commandes_formatees = []
        total_depense = 0.0

        for commande in commandes_domaine:
            commande_dict = {
                "commande_id": str(commande.id),
                "checkout_id": str(commande.checkout_id),
                "statut": commande.statut,
                "date_commande": commande.date_commande.isoformat(),
                "date_modification": commande.date_modification.isoformat(),
                "montants": {
                    "sous_total": float(commande.sous_total),
                    "frais_livraison": float(commande.frais_livraison),
                    "total": float(commande.total),
                    "livraison_gratuite": commande.frais_livraison == 0,
                },
                "details": {
                    "nombre_articles": commande.nombre_articles,
                    "nombre_produits": commande.nombre_produits,
                    "notes": commande.notes,
                },
                "adresse_livraison": (
                    commande.adresse_livraison.to_dict()
                    if commande.adresse_livraison
                    else None
                ),
                "produits": [
                    {
                        "produit_id": str(ligne.produit_id),
                        "nom_produit": ligne.nom_produit,
                        "quantite": ligne.quantite,
                        "prix_unitaire": float(ligne.prix_unitaire),
                        "prix_total": float(ligne.prix_total()),
                    }
                    for ligne in commande.lignes
                ],
            }

            commandes_formatees.append(commande_dict)
            total_depense += float(commande.total)

        # Calcul des statistiques
        nombre_commandes = len(commandes_formatees)
        commande_moyenne = (
            total_depense / nombre_commandes if nombre_commandes > 0 else 0.0
        )
        derniere_commande = (
            commandes_formatees[0]["date_commande"] if commandes_formatees else None
        )

        logger.debug(
            f"Historique récupéré: {nombre_commandes} commandes, total {total_depense}€"
        )

        return {
            "client_id": client_id,
            "commandes": commandes_formatees,
            "statistiques": {
                "nombre_commandes": nombre_commandes,
                "total_depense": round(total_depense, 2),
                "commande_moyenne": round(commande_moyenne, 2),
                "derniere_commande": derniere_commande,
            },
        }
