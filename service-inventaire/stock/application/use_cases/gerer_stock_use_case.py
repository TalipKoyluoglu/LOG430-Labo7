"""
Use Case pour la gestion des stocks
Contient toute la logique métier pour les opérations sur les stocks central et local.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..repositories.stock_repository import StockRepository
from ..repositories.demande_repository import DemandeRepository
from ..services.produit_service import ProduitService
from ..services.magasin_service import MagasinService

from ...domain.entities import (
    StockCentral,
    StockLocal,
    DemandeReapprovisionnement,
    StatutDemandeStock,
    TransfertStock,
    InventaireMagasin,
)
from ...domain.value_objects import ProduitId, MagasinId, Quantite, StockId, DemandeId
from ...domain.exceptions import (
    StockInsuffisantError,
    InventaireDomainError,
    ProduitInexistantError,
    MagasinInexistantError,
)


@dataclass
class AugmenterStockRequest:
    """DTO pour les demandes d'augmentation de stock"""

    produit_id: str  # Changé pour supporter les UUID
    quantite: int
    magasin_id: Optional[str] = None  # None = stock central


@dataclass
class DiminuerStockRequest:
    """DTO pour les demandes de diminution de stock"""

    produit_id: str  # Changé pour supporter les UUID
    quantite: int
    magasin_id: Optional[str] = None  # None = stock central


@dataclass
class ConsulterStockResponse:
    """DTO pour la réponse de consultation de stock"""

    produit_id: str
    quantite: int
    niveau: str
    magasin_id: Optional[str] = None
    nom_produit: Optional[str] = None
    nom_magasin: Optional[str] = None


class GererStockUseCase:
    """
    Use Case principal pour toutes les opérations de gestion de stock.
    Implémente toute la logique métier existante dans une architecture DDD.
    """

    def __init__(
        self,
        stock_repository: StockRepository,
        demande_repository: DemandeRepository,
        produit_service: ProduitService,
        magasin_service: MagasinService,
    ):
        self.stock_repository = stock_repository
        self.demande_repository = demande_repository
        self.produit_service = produit_service
        self.magasin_service = magasin_service

    def augmenter_stock(self, request: AugmenterStockRequest) -> Dict[str, Any]:
        """
        Règle métier : Augmente le stock (central ou local) d'un produit
        Fonctionnalité équivalente à l'API /increase_stock/
        """
        produit_id = ProduitId(request.produit_id)
        quantite = Quantite.from_int(request.quantite)

        # Validation métier
        self.produit_service.valider_produit_existe(produit_id)

        if request.magasin_id is None:
            # Augmenter stock central
            return self._augmenter_stock_central(produit_id, quantite)
        else:
            # Augmenter stock local
            magasin_id = MagasinId(request.magasin_id)
            self.magasin_service.valider_magasin_existe(magasin_id)
            return self._augmenter_stock_local(produit_id, magasin_id, quantite)

    def diminuer_stock(self, request: DiminuerStockRequest) -> Dict[str, Any]:
        """
        Règle métier : Diminue le stock (central ou local) d'un produit
        Fonctionnalité équivalente à l'API /decrease_stock/
        """
        produit_id = ProduitId(request.produit_id)
        quantite = Quantite.from_int(request.quantite)

        # Validation métier
        self.produit_service.valider_produit_existe(produit_id)

        if request.magasin_id is None:
            # Diminuer stock central
            return self._diminuer_stock_central(produit_id, quantite)
        else:
            # Diminuer stock local
            magasin_id = MagasinId(request.magasin_id)
            self.magasin_service.valider_magasin_existe(magasin_id)
            return self._diminuer_stock_local(produit_id, magasin_id, quantite)

    def consulter_stock(
        self, produit_id: str, magasin_id: Optional[str] = None
    ) -> ConsulterStockResponse:
        """
        Règle métier : Consulte le stock d'un produit (central ou local)
        Fonctionnalité équivalente aux APIs /stock_central/ et /stock_local/
        """
        produit_id_vo = ProduitId(produit_id)
        self.produit_service.valider_produit_existe(produit_id_vo)

        if magasin_id is None:
            # Stock central
            stock = self.stock_repository.get_stock_central_by_produit(produit_id_vo)
            if not stock:
                return ConsulterStockResponse(
                    produit_id=str(produit_id),
                    quantite=0,
                    niveau="Indisponible",
                    nom_produit=self.produit_service.get_nom_produit(produit_id_vo),
                )

            return ConsulterStockResponse(
                produit_id=str(produit_id),
                quantite=int(stock.quantite),
                niveau=self._evaluer_niveau_stock_central(stock.quantite),
                nom_produit=self.produit_service.get_nom_produit(produit_id_vo),
            )
        else:
            # Stock local
            magasin_id_vo = MagasinId(magasin_id)
            self.magasin_service.valider_magasin_existe(magasin_id_vo)

            stock = self.stock_repository.get_stock_local_by_produit_magasin(
                produit_id_vo, magasin_id_vo
            )
            if not stock:
                return ConsulterStockResponse(
                    produit_id=str(produit_id),
                    quantite=0,
                    niveau="Indisponible",
                    magasin_id=str(magasin_id),
                    nom_produit=self.produit_service.get_nom_produit(produit_id_vo),
                    nom_magasin=self.magasin_service.get_nom_magasin(magasin_id_vo),
                )

            return ConsulterStockResponse(
                produit_id=str(produit_id),
                quantite=int(stock.quantite),
                niveau=stock.get_niveau_stock(),
                magasin_id=str(magasin_id),
                nom_produit=self.produit_service.get_nom_produit(produit_id_vo),
                nom_magasin=self.magasin_service.get_nom_magasin(magasin_id_vo),
            )

    def lister_tous_stocks_centraux(self) -> List[ConsulterStockResponse]:
        """
        Règle métier : Liste tous les stocks centraux
        Fonctionnalité équivalente à l'API /stocks_centraux/
        """
        stocks = self.stock_repository.get_all_stocks_centraux()
        return [
            ConsulterStockResponse(
                produit_id=str(stock.produit_id),
                quantite=int(stock.quantite),
                niveau=self._evaluer_niveau_stock_central(stock.quantite),
                nom_produit=self.produit_service.get_nom_produit(stock.produit_id),
            )
            for stock in stocks
        ]

    def lister_stocks_locaux_magasin(
        self, magasin_id: int
    ) -> List[ConsulterStockResponse]:
        """
        Règle métier : Liste tous les stocks locaux d'un magasin
        Fonctionnalité équivalente à l'API /stocks_locaux/{magasin_id}/
        """
        magasin_id_vo = MagasinId(magasin_id)
        self.magasin_service.valider_magasin_existe(magasin_id_vo)

        stocks = self.stock_repository.get_all_stocks_locaux_by_magasin(magasin_id_vo)
        nom_magasin = self.magasin_service.get_nom_magasin(magasin_id_vo)

        return [
            ConsulterStockResponse(
                produit_id=str(stock.produit_id),
                quantite=int(stock.quantite),
                niveau=stock.get_niveau_stock(),
                magasin_id=str(magasin_id),
                nom_produit=self.produit_service.get_nom_produit(stock.produit_id),
                nom_magasin=nom_magasin,
            )
            for stock in stocks
        ]

    def lister_tous_stocks_par_magasin(self) -> Dict[str, Any]:
        """
        Règle métier : Liste tous les magasins avec leurs stocks locaux
        Fonctionnalité nouvelle pour avoir une vue globale des stocks par magasin
        """
        # Récupérer tous les stocks locaux
        tous_stocks_locaux = self.stock_repository.get_all_stocks_locaux()

        # Grouper par magasin
        stocks_par_magasin = {}
        for stock in tous_stocks_locaux:
            magasin_id_str = str(stock.magasin_id)

            if magasin_id_str not in stocks_par_magasin:
                stocks_par_magasin[magasin_id_str] = {
                    "magasin_id": magasin_id_str,
                    "nom_magasin": self.magasin_service.get_nom_magasin(
                        stock.magasin_id
                    ),
                    "stocks": [],
                }

            stocks_par_magasin[magasin_id_str]["stocks"].append(
                {
                    "produit_id": str(stock.produit_id),
                    "quantite": int(stock.quantite),
                    "niveau": stock.get_niveau_stock(),
                    "nom_produit": self.produit_service.get_nom_produit(
                        stock.produit_id
                    ),
                }
            )

        return {
            "magasins": list(stocks_par_magasin.values()),
            "total_magasins": len(stocks_par_magasin),
        }

    # Méthodes privées pour l'implémentation

    def _augmenter_stock_central(
        self, produit_id: ProduitId, quantite: Quantite
    ) -> Dict[str, Any]:
        """Augmente le stock central avec gestion de création si nécessaire"""
        stock = self.stock_repository.get_stock_central_by_produit(produit_id)

        if stock is None:
            # Créer nouveau stock central
            stock = StockCentral(
                stock_id=StockId.generate(),
                produit_id=produit_id,
                quantite=quantite,
                created_at=datetime.now(),
            )
        else:
            # Augmenter stock existant
            stock.augmenter(quantite)

        stock_sauve = self.stock_repository.save_stock_central(stock)

        return {
            "success": True,
            "message": f"Stock central du produit {produit_id} augmenté de {quantite}",
            "nouvelle_quantite": int(stock_sauve.quantite),
            "niveau": self._evaluer_niveau_stock_central(stock_sauve.quantite),
        }

    def _diminuer_stock_central(
        self, produit_id: ProduitId, quantite: Quantite
    ) -> Dict[str, Any]:
        """Diminue le stock central avec validation métier"""
        stock = self.stock_repository.get_stock_central_by_produit(produit_id)

        if stock is None:
            raise StockInsuffisantError(
                f"Aucun stock central trouvé pour le produit {produit_id}"
            )

        stock.diminuer(quantite)  # Validation métier dans l'entité
        stock_sauve = self.stock_repository.save_stock_central(stock)

        return {
            "success": True,
            "message": f"Stock central du produit {produit_id} diminué de {quantite}",
            "nouvelle_quantite": int(stock_sauve.quantite),
            "niveau": self._evaluer_niveau_stock_central(stock_sauve.quantite),
        }

    def _augmenter_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> Dict[str, Any]:
        """Augmente le stock local avec gestion de création si nécessaire"""
        stock = self.stock_repository.get_stock_local_by_produit_magasin(
            produit_id, magasin_id
        )

        if stock is None:
            # Créer nouveau stock local
            stock = StockLocal(
                stock_id=StockId.generate(),
                produit_id=produit_id,
                magasin_id=magasin_id,
                quantite=quantite,
                created_at=datetime.now(),
            )
        else:
            # Augmenter stock existant
            stock.augmenter(quantite)

        stock_sauve = self.stock_repository.save_stock_local(stock)

        return {
            "success": True,
            "message": f"Stock local du produit {produit_id} au magasin {magasin_id} augmenté de {quantite}",
            "nouvelle_quantite": int(stock_sauve.quantite),
            "niveau": stock_sauve.get_niveau_stock(),
        }

    def _diminuer_stock_local(
        self, produit_id: ProduitId, magasin_id: MagasinId, quantite: Quantite
    ) -> Dict[str, Any]:
        """Diminue le stock local avec validation métier"""
        stock = self.stock_repository.get_stock_local_by_produit_magasin(
            produit_id, magasin_id
        )

        if stock is None:
            raise StockInsuffisantError(
                f"Aucun stock local trouvé pour le produit {produit_id} au magasin {magasin_id}"
            )

        stock.diminuer(quantite)  # Validation métier dans l'entité
        stock_sauve = self.stock_repository.save_stock_local(stock)

        return {
            "success": True,
            "message": f"Stock local du produit {produit_id} au magasin {magasin_id} diminué de {quantite}",
            "nouvelle_quantite": int(stock_sauve.quantite),
            "niveau": stock_sauve.get_niveau_stock(),
        }

    def _evaluer_niveau_stock_central(self, quantite: Quantite) -> str:
        """Évalue le niveau du stock central selon les règles métier"""
        if quantite.est_critique(seuil=5):
            return "Critique"
        elif quantite.est_faible(seuil=10):
            return "Bas"
        elif quantite.est_importante(seuil=100):
            return "Élevé"
        else:
            return "Normal"
