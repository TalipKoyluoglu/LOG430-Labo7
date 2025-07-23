"""
Client HTTP pour le Service Commandes via Kong API Gateway
Communication avec les endpoints DDD du service-commandes
"""

import requests
import logging
from typing import Dict, List, Optional, Any
import uuid

logger = logging.getLogger(__name__)

BASE_URL = "http://kong:8000/api/commandes"


class CommandesClient:
    """
    Client HTTP pour communiquer avec le service-commandes
    Encapsule tous les appels REST vers les endpoints DDD des ventes
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

    def enregistrer_vente(
        self, magasin_id: str, produit_id: str, quantite: int, client_id: str
    ) -> Dict[str, Any]:
        """
        POST /api/v1/ventes-ddd/enregistrer/
        Use Case: EnregistrerVenteUseCase

        Args:
            magasin_id: UUID du magasin où effectuer la vente
            produit_id: UUID du produit à vendre
            quantite: Quantité à vendre (doit être positive)
            client_id: UUID du client (obligatoire pour traçabilité)

        Returns:
            Dict avec le résultat de l'enregistrement de la vente
        """
        logger.info(
            "💰 Client API: Enregistrement vente P%s (Qté: %s)", produit_id, quantite
        )
        try:
            data = {
                "magasin_id": magasin_id,
                "produit_id": produit_id,
                "quantite": quantite,
                "client_id": client_id,
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/ventes-ddd/enregistrer/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur enregistrement vente: {e}")
            return {
                "success": False,
                "error": f"Erreur lors de l'enregistrement de la vente: {str(e)}",
            }

    def annuler_vente(self, vente_id: str, motif: str) -> Dict[str, Any]:
        """
        PATCH /api/v1/ventes-ddd/<id>/annuler/
        Use Case: AnnulerVenteUseCase

        Args:
            vente_id: UUID de la vente à annuler
            motif: Motif de l'annulation

        Returns:
            Dict avec le résultat de l'annulation
        """
        try:
            data = {"motif": motif}

            response = self.session.patch(
                f"{self.base_url}/api/v1/ventes-ddd/{vente_id}/annuler/", json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur annulation vente {vente_id}: {e}")
            return {
                "success": False,
                "error": f"Erreur lors de l'annulation de la vente: {str(e)}",
            }

    def lister_toutes_ventes(self) -> Dict[str, Any]:
        """
        GET /api/v1/ventes-ddd/
        Récupère la liste de toutes les ventes avec détails complets

        Returns:
            Dict avec la liste des ventes et métadonnées
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/ventes-ddd/")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération toutes ventes: {e}")
            return {
                "success": False,
                "ventes": [],
                "total_ventes": 0,
                "error": f"Erreur lors de la récupération des ventes: {str(e)}",
            }

    def consulter_vente(self, vente_id: str) -> Dict[str, Any]:
        """
        GET /api/v1/ventes-ddd/<id>/
        Récupère les détails d'une vente spécifique par son ID

        Args:
            vente_id: UUID de la vente à consulter

        Returns:
            Dict avec les détails de la vente ou erreur
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/ventes-ddd/{vente_id}/"
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur consultation vente {vente_id}: {e}")
            return {
                "success": False,
                "error": f"Vente {vente_id} non trouvée: {str(e)}",
            }

    def generer_indicateurs(self) -> Dict[str, Any]:
        """
        GET /api/v1/indicateurs/
        Use Case: GenererIndicateursUseCase
        Génère les indicateurs de performance par magasin avec logique métier DDD

        Returns:
            Dict avec les indicateurs de performance de tous les magasins
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/indicateurs/")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur génération indicateurs: {e}")
            return {
                "success": False,
                "indicateurs": [],
                "error": f"Erreur lors de la génération des indicateurs: {str(e)}",
            }

    def generer_rapport_consolide(self) -> Dict[str, Any]:
        """
        GET /api/v1/rapport-consolide/
        Use Case: GenererRapportConsolideUseCase (UC1)
        Génère le rapport consolidé avec analyse de performance et alertes métier

        Returns:
            Dict avec le rapport consolidé tous magasins
        """
        logger.info("📊 Client API: Génération rapport consolidé")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/rapport-consolide/")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur génération rapport consolidé: {e}")
            return {
                "success": False,
                "rapport": {},
                "error": f"Erreur lors de la génération du rapport consolidé: {str(e)}",
            }

    def obtenir_ventes_par_magasin(self, magasin_id: str) -> List[Dict[str, Any]]:
        """
        Filtre les ventes d'un magasin spécifique depuis toutes les ventes

        Args:
            magasin_id: UUID du magasin

        Returns:
            Liste des ventes du magasin spécifié
        """
        try:
            toutes_ventes = self.lister_toutes_ventes()
            if toutes_ventes.get("success", False):
                ventes = toutes_ventes.get("ventes", [])
                ventes_magasin = [
                    vente for vente in ventes if vente.get("magasin_id") == magasin_id
                ]
                return ventes_magasin
            else:
                logger.warning(f"Échec récupération ventes magasin {magasin_id}")
                return []

        except Exception as e:
            logger.error(f"Erreur récupération ventes magasin {magasin_id}: {e}")
            return []

    def obtenir_statistiques_ventes(self) -> Dict[str, Any]:
        """
        Calcule des statistiques générales sur toutes les ventes

        Returns:
            Dict avec statistiques agrégées des ventes
        """
        try:
            toutes_ventes = self.lister_toutes_ventes()
            if not toutes_ventes.get("success", False):
                return {"error": "Impossible de récupérer les ventes"}

            ventes = toutes_ventes.get("ventes", [])

            # Calculs statistiques
            total_ventes = len(ventes)
            chiffre_affaires_total = sum(vente.get("total", 0) for vente in ventes)
            ventes_actives = [v for v in ventes if v.get("statut") == "active"]
            ventes_annulees = [v for v in ventes if v.get("statut") == "annulee"]

            return {
                "total_ventes": total_ventes,
                "ventes_actives": len(ventes_actives),
                "ventes_annulees": len(ventes_annulees),
                "chiffre_affaires_total": chiffre_affaires_total,
                "chiffre_affaires_actif": sum(
                    v.get("total", 0) for v in ventes_actives
                ),
            }

        except Exception as e:
            logger.error(f"Erreur calcul statistiques ventes: {e}")
            return {"error": f"Erreur calcul statistiques: {str(e)}"}

    def lister_magasins(self) -> Dict[str, Any]:
        """
        GET /api/v1/magasins/
        Récupère la liste des magasins avec leurs vrais UUIDs depuis le service-commandes
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/magasins/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des magasins: {e}")
            return {"success": False, "magasins": [], "error": str(e)}
