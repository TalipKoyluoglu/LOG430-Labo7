"""
Client HTTP pour le Service Inventaire via Kong API Gateway
Communication avec les endpoints DDD du service-inventaire
"""

import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

BASE_URL = "http://kong:8000/api/inventaire"


class InventaireClient:
    """
    Client HTTP pour communiquer avec le service-inventaire
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

    def health_check(self) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/health-check/
        Vérification de l'état du service inventaire
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/health-check/"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur health check inventaire: {e}")
            return {"status": "error", "message": str(e)}

    # === GESTION DES STOCKS ===

    def augmenter_stock(
        self, produit_id: int, quantite: int, magasin_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        POST /api/ddd/inventaire/augmenter-stock/
        Augmente le stock d'un produit (central ou local)
        """
        try:
            data = {"produit_id": produit_id, "quantite": quantite}
            if magasin_id:
                data["magasin_id"] = magasin_id

            response = self.session.post(
                f"{self.base_url}/api/ddd/inventaire/augmenter-stock/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur augmentation stock: {e}")
            return {"success": False, "error": str(e)}

    def diminuer_stock(
        self, produit_id: int, quantite: int, magasin_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        POST /api/ddd/inventaire/diminuer-stock/
        Diminue le stock d'un produit (central ou local)
        """
        try:
            data = {"produit_id": produit_id, "quantite": quantite}
            if magasin_id:
                data["magasin_id"] = magasin_id

            response = self.session.post(
                f"{self.base_url}/api/ddd/inventaire/diminuer-stock/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur diminution stock: {e}")
            return {"success": False, "error": str(e)}

    def consulter_stock_central(self, produit_id: int) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/stock-central/<produit_id>/
        Consulte le stock central d'un produit
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/stock-central/{produit_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur consultation stock central {produit_id}: {e}")
            return {"success": False, "error": str(e)}

    def consulter_stock_local(self, produit_id: int, magasin_id: int) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/stock-local/<produit_id>/<magasin_id>/
        Consulte le stock local d'un produit dans un magasin
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/stock-local/{produit_id}/{magasin_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Erreur consultation stock local {produit_id}/{magasin_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    def lister_stocks_centraux(self) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/stocks-centraux/
        Liste tous les stocks centraux
        """
        logger.info("🏪 Client API: Récupération stocks centraux")
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/stocks-centraux/"
            )
            response.raise_for_status()
            data = response.json()

            # L'API retourne {"stocks": [...]} sans clé success, on l'ajoute
            if "success" not in data:
                data["success"] = True

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste stocks centraux: {e}")
            return {"success": False, "stocks": [], "error": str(e)}

    def lister_stocks_locaux_magasin(self, magasin_id: int) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/stocks-locaux/<magasin_id>/
        Liste les stocks locaux d'un magasin
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/stocks-locaux/{magasin_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste stocks magasin {magasin_id}: {e}")
            return {"success": False, "stocks": [], "error": str(e)}

    def lister_tous_magasins_avec_stocks(self) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/tous-magasins-stocks/
        Liste tous les magasins avec leurs stocks locaux
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/tous-magasins-stocks/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste tous magasins stocks: {e}")
            return {"success": False, "magasins": [], "error": str(e)}

    # === GESTION DES DEMANDES ===

    def creer_demande_reapprovisionnement(
        self, produit_id: str, magasin_id: str, quantite: int
    ) -> Dict[str, Any]:
        """
        POST /api/ddd/inventaire/demandes/
        Crée une nouvelle demande de réapprovisionnement
        """
        logger.info(
            "🔄 Client API: Création demande réapprovisionnement P%s M%s",
            produit_id,
            magasin_id,
        )
        try:
            data = {
                "produit_id": produit_id,
                "magasin_id": magasin_id,
                "quantite": quantite,
            }

            response = self.session.post(
                f"{self.base_url}/api/ddd/inventaire/demandes/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    f"Erreur création demande: {e} | Réponse: {e.response.text}"
                )
            else:
                logger.error(f"Erreur création demande: {e}")
            return {"success": False, "error": str(e)}

    def lister_demandes_en_attente(self) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/demandes/en-attente/
        Liste toutes les demandes en attente
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/demandes/en-attente/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste demandes en attente: {e}")
            return {"success": False, "demandes": [], "error": str(e)}

    def lister_demandes_par_magasin(self, magasin_id: int) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/demandes/magasin/<magasin_id>/
        Liste toutes les demandes d'un magasin spécifique
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/demandes/magasin/{magasin_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur liste demandes magasin {magasin_id}: {e}")
            return {"success": False, "demandes": [], "error": str(e)}

    def obtenir_demande_par_id(self, demande_id: str) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/demandes/<demande_id>/
        Récupère une demande spécifique par son ID
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/demandes/{demande_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur obtention demande {demande_id}: {e}")
            return {"success": False, "error": str(e)}

    def supprimer_demande(self, demande_id: str) -> Dict[str, Any]:
        """
        DELETE /api/ddd/inventaire/demandes/<demande_id>/
        Supprime une demande (seulement si en attente)
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/ddd/inventaire/demandes/{demande_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur suppression demande {demande_id}: {e}")
            return {"success": False, "error": str(e)}

    def approuver_demande(self, demande_id: str) -> Dict[str, Any]:
        """
        PUT /api/ddd/inventaire/demandes/<demande_id>/approuver/
        Approuve une demande de réapprovisionnement
        """
        try:
            response = self.session.put(
                f"{self.base_url}/api/ddd/inventaire/demandes/{demande_id}/approuver/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur approbation demande {demande_id}: {e}")
            return {"success": False, "error": str(e)}

    def rejeter_demande(self, demande_id: str) -> Dict[str, Any]:
        """
        PUT /api/ddd/inventaire/demandes/<demande_id>/rejeter/
        Rejette une demande de réapprovisionnement
        """
        try:
            response = self.session.put(
                f"{self.base_url}/api/ddd/inventaire/demandes/{demande_id}/rejeter/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur rejet demande {demande_id}: {e}")
            return {"success": False, "error": str(e)}

    def analyser_besoins_reapprovisionnement(self, magasin_id: int) -> Dict[str, Any]:
        """
        GET /api/ddd/inventaire/analyser-besoins/<magasin_id>/
        Analyse les besoins de réapprovisionnement d'un magasin
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/ddd/inventaire/analyser-besoins/{magasin_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur analyse besoins magasin {magasin_id}: {e}")
            return {"success": False, "error": str(e)}
