"""
Use Case: Générer Indicateurs de Performance
Fonctionnalité métier complète pour générer les rapports de performance
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..repositories.vente_repository import VenteRepository
from ..repositories.magasin_repository import MagasinRepository
from ..services.stock_service import StockService
from ..services.produit_service import ProduitService
from ...domain.entities import Magasin


class GenererIndicateursUseCase:
    """
    Use Case: Générer les indicateurs de performance par magasin

    Orchestration complète de la fonctionnalité métier:
    1. Récupération de tous les magasins
    2. Calcul du chiffre d'affaires (ventes actives uniquement)
    3. Analyse du stock (ruptures/surstock)
    4. Calcul des tendances (top produits semaine)
    5. Agrégation des indicateurs
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
        Exécute le cas d'usage de génération d'indicateurs

        Returns:
            Liste des indicateurs par magasin
        """

        # 1. Récupération de tous les magasins
        magasins = self._magasin_repo.get_all()

        # 2. Calcul de la période d'analyse (7 derniers jours)
        fin_periode = datetime.now()
        debut_periode = fin_periode - timedelta(days=7)

        indicateurs = []

        for magasin in magasins:
            # 3. Calcul du chiffre d'affaires (ventes actives sur la même période que tendances)
            chiffre_affaires = self._calculer_chiffre_affaires(
                magasin, debut_periode, fin_periode
            )

            # 4. Analyse du stock (métier: ruptures et surstock)
            ruptures, surstock = self._analyser_stock(magasin)

            # 5. Calcul des tendances (métier: top 3 produits de la semaine)
            tendances = self._calculer_tendances(magasin, debut_periode, fin_periode)

            # 6. Agrégation des indicateurs
            indicateurs.append(
                {
                    "magasin": magasin.nom,
                    "chiffre_affaires": float(chiffre_affaires),
                    "ruptures": ruptures,
                    "surstock": surstock,
                    "tendances": tendances,
                }
            )

        return indicateurs

    def _calculer_chiffre_affaires(
        self, magasin: Magasin, debut_periode: datetime, fin_periode: datetime
    ) -> float:
        """
        Calcule le chiffre d'affaires du magasin sur une période (ventes actives uniquement)
        """
        ventes_periode = self._vente_repo.get_ventes_actives_by_magasin_and_period(
            magasin.id, debut_periode, fin_periode
        )
        total = 0.0
        for vente in ventes_periode:
            total += float(vente.calculer_total())
        return total

    def _analyser_stock(self, magasin: Magasin) -> tuple[int, int]:
        """
        Analyse le stock pour détecter ruptures et surstock
        Règles métier:
        - Rupture = stock = 0
        - Surstock = stock > 10
        """
        stocks = self._stock_service.get_all_stock_local(magasin.id)

        ruptures = 0
        surstock = 0

        for stock_info in stocks:
            if stock_info.quantite_disponible == 0:
                ruptures += 1
            elif stock_info.quantite_disponible > 10:
                surstock += 1

        return ruptures, surstock

    def _calculer_tendances(
        self, magasin: Magasin, debut: datetime, fin: datetime
    ) -> str:
        """
        Calcule les tendances de vente (top 3 produits de la période)
        Règle métier: Seules les ventes actives comptent
        """
        ventes_periode = self._vente_repo.get_ventes_actives_by_magasin_and_period(
            magasin.id, debut, fin
        )

        # Comptage des produits vendus
        produits_vendus = {}
        produits_noms = {}  # Cache des noms de produits

        for vente in ventes_periode:
            for ligne in vente.lignes:
                produit_id = ligne.produit_id

                # Récupération du nom du produit (avec cache)
                if produit_id not in produits_noms:
                    produit_info = self._produit_service.get_produit_details(produit_id)
                    produits_noms[produit_id] = (
                        produit_info.nom if produit_info else f"Produit {produit_id}"
                    )

                nom_produit = produits_noms[produit_id]
                produits_vendus[nom_produit] = (
                    produits_vendus.get(nom_produit, 0) + ligne.quantite
                )

        # Top 3 produits
        top_produits = sorted(
            produits_vendus.items(), key=lambda x: x[1], reverse=True
        )[:3]

        if not top_produits:
            return "Aucune vente cette semaine"

        return ", ".join([f"{nom} ({quantite})" for nom, quantite in top_produits])
