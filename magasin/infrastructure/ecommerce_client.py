"""
Client HTTP pour le Service E-commerce via Kong API Gateway
Communication avec les endpoints DDD du service-ecommerce
"""

import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

BASE_URL = "http://kong:8000/api/ecommerce"


class EcommerceClient:
    """
    Client HTTP pour communiquer avec le service-ecommerce
    Encapsule tous les appels REST vers les endpoints DDD
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-Key": "magasin-secret-key-2025",  # Clé API Kong
            }
        )

    # === GESTION DES CLIENTS ===

    def creer_compte_client(
        self,
        prenom: str,
        nom: str,
        email: str,
        adresse_rue: str,
        adresse_ville: str,
        adresse_code_postal: str,
        telephone: Optional[str] = None,
        adresse_province: str = "Québec",
        adresse_pays: str = "Canada",
    ) -> Dict[str, Any]:
        """
        POST /api/clients/
        Use Case: CreerCompteClientUseCase
        """
        logger.info("👤 Client API: Création compte client '%s %s'", prenom, nom)
        try:
            data = {
                "prenom": prenom,
                "nom": nom,
                "email": email,
                "adresse_rue": adresse_rue,
                "adresse_ville": adresse_ville,
                "adresse_code_postal": adresse_code_postal,
                "adresse_province": adresse_province,
                "adresse_pays": adresse_pays,
            }
            if telephone:
                data["telephone"] = telephone

            response = self.session.post(f"{self.base_url}/api/clients/", json=data)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur création compte client: {e}")
            return {"success": False, "error": str(e)}

    def lister_clients(self) -> Dict[str, Any]:
        """
        GET /api/clients/
        Use Case: ListerClientsUseCase
        """
        try:
            response = self.session.get(f"{self.base_url}/api/clients/")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste clients: {e}")
            return {"success": False, "clients": [], "error": str(e)}

    def valider_client(self, client_id: str) -> Dict[str, Any]:
        """
        GET /api/clients/<client_id>/valider/
        Use Case: ValiderClientUseCase
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/clients/{client_id}/valider/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur validation client {client_id}: {e}")
            return {"valid": False, "error": str(e)}

    # === GESTION DU PANIER ===

    def voir_panier(self, client_id: str) -> Dict[str, Any]:
        """
        GET /api/panier/clients/<client_id>/panier/
        Use Case: VoirPanierUseCase
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/panier/clients/{client_id}/panier/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur consultation panier {client_id}: {e}")
            return {"success": False, "error": str(e)}

    def ajouter_produit_panier(
        self, client_id: str, produit_id: str, quantite: int
    ) -> Dict[str, Any]:
        """
        POST /api/panier/clients/<client_id>/panier/
        Use Case: AjouterProduitPanierUseCase
        """
        try:
            data = {"produit_id": produit_id, "quantite": quantite}

            response = self.session.post(
                f"{self.base_url}/api/panier/clients/{client_id}/panier/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur ajout produit panier: {e}")
            return {"success": False, "error": str(e)}

    def vider_panier(self, client_id: str) -> Dict[str, Any]:
        """
        DELETE /api/panier/clients/<client_id>/panier/
        Use Case: ViderPanierUseCase
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/panier/clients/{client_id}/panier/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur vidage panier {client_id}: {e}")
            return {"success": False, "error": str(e)}

    def modifier_quantite_panier(
        self, client_id: str, produit_id: str, quantite: int
    ) -> Dict[str, Any]:
        """
        PUT /api/panier/clients/<client_id>/panier/<produit_id>/
        Use Case: ModifierQuantitePanierUseCase
        """
        try:
            data = {"quantite": quantite}

            response = self.session.put(
                f"{self.base_url}/api/panier/clients/{client_id}/panier/{produit_id}/",
                json=data,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur modification quantité panier: {e}")
            return {"success": False, "error": str(e)}

    # === CHECKOUT ET COMMANDES ===

    def checkout_ecommerce(
        self,
        client_id: str,
        adresse_livraison: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /api/commandes/clients/<client_id>/checkout/
        Use Case: CheckoutEcommerceUseCase
        """
        logger.info("🛒 Client API: Checkout e-commerce client %s", client_id)
        try:
            data = {}
            if adresse_livraison:
                data["adresse_livraison"] = adresse_livraison
            if notes:
                data["notes"] = notes

            response = self.session.post(
                f"{self.base_url}/api/commandes/clients/{client_id}/checkout/",
                json=data,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur checkout client {client_id}: {e}")
            return {"success": False, "error": str(e)}

    def verifier_prerequis_checkout(self, client_id: str) -> Dict[str, Any]:
        """
        GET /api/commandes/clients/<client_id>/checkout/prerequis/
        Vérifie les prérequis pour le check-out
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/commandes/clients/{client_id}/checkout/prerequis/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur vérification prérequis checkout {client_id}: {e}")
            return {"peut_commander": False, "error": str(e)}

    def historique_commandes_client(self, client_id: str) -> Dict[str, Any]:
        """
        GET /api/commandes/clients/<client_id>/historique/
        Récupère l'historique des commandes d'un client
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/commandes/clients/{client_id}/historique/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur historique commandes {client_id}: {e}")
            return {"success": False, "commandes": [], "error": str(e)}
