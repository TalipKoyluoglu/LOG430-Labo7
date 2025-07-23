"""
Service de communication avec le module panier local
Pour récupérer et valider les paniers lors du check-out
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

# Import local du module panier du service-ecommerce
from panier.application.use_cases.voir_panier_use_case import VoirPanierUseCase
from panier.application.use_cases.vider_panier_use_case import ViderPanierUseCase
from panier.infrastructure.django_panier_repository import DjangoPanierRepository

logger = logging.getLogger("commandes")


class PanierService:
    """
    Service pour communiquer avec le module panier local
    Gère la récupération et validation des paniers lors du check-out
    """

    def __init__(self):
        # Initialisation des use cases du module panier
        self.panier_repository = DjangoPanierRepository()
        self.voir_panier_use_case = VoirPanierUseCase(self.panier_repository)
        self.vider_panier_use_case = ViderPanierUseCase(self.panier_repository)

    def recuperer_panier_client(self, client_id: str) -> Dict[str, Any]:
        """
        Récupère le panier d'un client avec tous ses produits

        Args:
            client_id: UUID du client

        Returns:
            Dict avec les informations du panier
        """
        try:
            # Utiliser le use case existant du module panier
            client_uuid = UUID(client_id) if isinstance(client_id, str) else client_id
            resultat = self.voir_panier_use_case.execute(client_uuid)

            # Le VoirPanierUseCase retourne directement les données (pas de clé 'success')
            if resultat.get("panier_existe", False):
                return {
                    "success": True,
                    "panier_existe": True,
                    "panier_vide": resultat.get("est_vide", True),
                    "client_id": client_id,
                    "nombre_articles": resultat.get("resume", {}).get(
                        "nombre_articles", 0
                    ),
                    "nombre_produits": resultat.get("resume", {}).get(
                        "nombre_produits_differents", 0
                    ),
                    "total": resultat.get("resume", {}).get("prix_total", 0.0),
                    "produits": [
                        {
                            "produit_id": produit["produit_id"],
                            "nom_produit": produit["nom_produit"],
                            "quantite": produit["quantite"],
                            "prix_unitaire": produit["prix_unitaire"],
                            "prix_total": produit[
                                "prix_ligne"
                            ],  # Note: dans VoirPanierUseCase c'est 'prix_ligne'
                        }
                        for produit in resultat.get("produits", [])
                    ],
                }
            else:
                # Panier non trouvé ou vide
                return {
                    "success": True,
                    "panier_existe": False,
                    "panier_vide": True,
                    "client_id": client_id,
                    "nombre_articles": 0,
                    "nombre_produits": 0,
                    "total": 0.0,
                    "produits": [],
                    "message": "Panier non trouvé ou vide",
                }

        except Exception as e:
            logger.error(f"Erreur récupération panier client {client_id}: {e}")
            return {
                "success": False,
                "panier_existe": False,
                "panier_vide": True,
                "client_id": client_id,
                "error": f"Erreur lors de la récupération du panier: {str(e)}",
            }

    def valider_panier_pour_checkout(self, client_id: str) -> Dict[str, Any]:
        """
        Valide qu'un panier est prêt pour le check-out

        Args:
            client_id: UUID du client

        Returns:
            Dict avec le résultat de validation
        """
        panier_info = self.recuperer_panier_client(client_id)

        if not panier_info["success"]:
            return {
                "valide": False,
                "raison": "Erreur récupération panier",
                "details": panier_info.get("error", "Erreur inconnue"),
            }

        if not panier_info["panier_existe"]:
            return {
                "valide": False,
                "raison": "Panier inexistant",
                "details": f"Aucun panier trouvé pour le client {client_id}",
            }

        if panier_info["panier_vide"]:
            return {
                "valide": False,
                "raison": "Panier vide",
                "details": "Impossible de faire un check-out avec un panier vide",
            }

        if panier_info["total"] <= 0:
            return {
                "valide": False,
                "raison": "Total invalide",
                "details": f'Total du panier invalide: {panier_info["total"]}€',
            }

        return {
            "valide": True,
            "panier": panier_info,
            "resume": {
                "client_id": client_id,
                "nombre_articles": panier_info["nombre_articles"],
                "nombre_produits": panier_info["nombre_produits"],
                "total": panier_info["total"],
            },
        }

    def vider_panier_apres_commande(self, client_id: str) -> Dict[str, Any]:
        """
        Vide le panier d'un client après une commande réussie

        Args:
            client_id: UUID du client

        Returns:
            Dict avec le résultat de l'opération
        """
        try:
            # Utiliser le use case existant du module panier
            client_uuid = UUID(client_id) if isinstance(client_id, str) else client_id
            resultat = self.vider_panier_use_case.execute(client_uuid)

            if resultat["success"]:
                logger.info(f"Panier vidé après commande pour client {client_id}")
                return {
                    "success": True,
                    "message": "Panier vidé avec succès",
                    "statistiques": resultat.get("statistiques", {}),
                }
            else:
                logger.warning(
                    f"Échec vidage panier client {client_id}: {resultat.get('message')}"
                )
                return {
                    "success": False,
                    "error": resultat.get("message", "Erreur lors du vidage du panier"),
                }

        except Exception as e:
            logger.error(f"Erreur vidage panier client {client_id}: {e}")
            return {
                "success": False,
                "error": f"Erreur lors du vidage du panier: {str(e)}",
            }

    def obtenir_produits_pour_stock(self, client_id: str) -> list:
        """
        Obtient la liste des produits du panier au format pour vérification de stock

        Args:
            client_id: UUID du client

        Returns:
            Liste des produits formatés pour le service stock
        """
        panier_info = self.recuperer_panier_client(client_id)

        if (
            not panier_info["success"]
            or not panier_info["panier_existe"]
            or panier_info["panier_vide"]
        ):
            return []

        return [
            {
                "produit_id": produit["produit_id"],
                "quantite": produit["quantite"],
                "nom_produit": produit["nom_produit"],
            }
            for produit in panier_info["produits"]
        ]
