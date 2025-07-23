"""
Use Case: Générer Rapport Consolidé (UC1)
Fonctionnalité métier complète pour générer le rapport consolidé tous magasins
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from ..repositories.vente_repository import VenteRepository
from ..repositories.magasin_repository import MagasinRepository
from ..services.stock_service import StockService
from ..services.produit_service import ProduitService
from ...domain.entities import Magasin


class GenererRapportConsolideUseCase:
    """
    Use Case: Générer le rapport consolidé tous magasins (UC1)

    Retourne une liste simple de rapports par magasin avec:
    - total (chiffre d'affaires)
    - produits_vendus
    - stock_local
    """

    def __init__(
        self,
        vente_repository: VenteRepository,
        magasin_repository: MagasinRepository,
        stock_service: StockService,
        produit_service: ProduitService,
    ):
        self._vente_repo = vente_repository
        self._magasin_repo = magasin_repository
        self._stock_service = stock_service
        self._produit_service = produit_service

    def execute(self) -> List[Dict[str, Any]]:
        """
        Exécute le cas d'usage de génération du rapport consolidé

        Returns:
            Liste des rapports par magasin avec total, produits_vendus et stock_local
        """

        # Récupération de tous les magasins
        magasins = self._magasin_repo.get_all()

        # Définir la période d'analyse (7 derniers jours)
        fin_periode = datetime.now()
        debut_periode = fin_periode - timedelta(days=7)

        rapports = []

        for magasin in magasins:
            # Calcul du total (chiffre d'affaires sur la même période que produits_vendus)
            total = self._calculer_chiffre_affaires(magasin, debut_periode, fin_periode)

            # Liste des produits vendus
            produits_vendus = self._calculer_produits_vendus(
                magasin, debut_periode, fin_periode
            )

            # Informations stock local
            stock_local = self._calculer_stock_local(magasin)

            rapports.append(
                {
                    "magasin": magasin.nom,
                    "total": float(total),
                    "produits_vendus": produits_vendus,
                    "stock_local": stock_local,
                }
            )

        return rapports

    def _calculer_chiffre_affaires(
        self, magasin: Magasin, debut_periode: datetime, fin_periode: datetime
    ) -> Decimal:
        """Calcule le CA d'un magasin sur une période (ventes actives uniquement)"""
        ventes_periode = self._vente_repo.get_ventes_actives_by_magasin_and_period(
            magasin.id, debut_periode, fin_periode
        )
        total = sum(vente.calculer_total() for vente in ventes_periode)
        return Decimal(str(total)) if total else Decimal("0")

    def _calculer_produits_vendus(
        self, magasin: Magasin, debut_periode: datetime, fin_periode: datetime
    ) -> List[Dict[str, Any]]:
        """Calcule la liste des produits vendus par ce magasin sur une période"""
        ventes_periode = self._vente_repo.get_ventes_actives_by_magasin_and_period(
            magasin.id, debut_periode, fin_periode
        )
        produits_vendus = {}
        for vente in ventes_periode:
            for ligne in vente.lignes:
                produit_id = str(ligne.produit_id)
                # Récupération du nom du produit
                try:
                    produit_info = self._produit_service.get_produit_details(
                        ligne.produit_id
                    )
                    nom_produit = (
                        produit_info.nom if produit_info else f"Produit {produit_id}"
                    )
                except:
                    nom_produit = f"Produit {produit_id}"
                if produit_id not in produits_vendus:
                    produits_vendus[produit_id] = {
                        "produit_id": produit_id,
                        "nom": nom_produit,
                        "quantite_totale": 0,
                        "chiffre_affaires": 0.0,
                    }
                produits_vendus[produit_id]["quantite_totale"] += ligne.quantite
                produits_vendus[produit_id]["chiffre_affaires"] += float(
                    ligne.sous_total
                )
        return list(produits_vendus.values())

    def _calculer_stock_local(self, magasin: Magasin) -> Dict[str, Any]:
        """Calcule les informations de stock local pour ce magasin"""
        try:
            stocks = self._stock_service.get_all_stock_local(magasin.id)

            ruptures = 0
            surstock = 0
            produits_en_stock = len(stocks)

            for stock_info in stocks:
                if stock_info.quantite_disponible == 0:
                    ruptures += 1
                elif stock_info.quantite_disponible > 10:
                    surstock += 1

            return {
                "ruptures": ruptures,
                "surstock": surstock,
                "produits_en_stock": produits_en_stock,
            }
        except Exception as e:
            print(f"Erreur lors du calcul des stocks: {e}")
            return {"ruptures": 0, "surstock": 0, "produits_en_stock": 0}
