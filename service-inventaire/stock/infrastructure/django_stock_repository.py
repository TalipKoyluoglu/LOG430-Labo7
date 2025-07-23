"""
Implémentation Django du repository Stock
Convertit entre les modèles Django et les entités DDD.
"""

from typing import List, Optional
from datetime import datetime
import uuid

from django.core.exceptions import ObjectDoesNotExist

from ..models import StockCentral as DjangoStockCentral, StockLocal as DjangoStockLocal
from ..application.repositories.stock_repository import StockRepository
from ..domain.entities import StockCentral, StockLocal
from ..domain.value_objects import ProduitId, MagasinId, StockId, Quantite


class DjangoStockRepository(StockRepository):
    """Implémentation concrète du repository Stock utilisant Django ORM"""

    def get_stock_central_by_produit(
        self, produit_id: ProduitId
    ) -> Optional[StockCentral]:
        """Récupère le stock central d'un produit spécifique"""
        try:
            django_stock = DjangoStockCentral.objects.get(produit_id=str(produit_id))
            return self._mapper_stock_central_vers_domaine(django_stock)
        except ObjectDoesNotExist:
            return None

    def get_stock_local_by_produit_magasin(
        self, produit_id: ProduitId, magasin_id: MagasinId
    ) -> Optional[StockLocal]:
        """Récupère le stock local d'un produit dans un magasin spécifique"""
        try:
            django_stock = DjangoStockLocal.objects.get(
                produit_id=str(produit_id), magasin_id=str(magasin_id)
            )
            return self._mapper_stock_local_vers_domaine(django_stock)
        except ObjectDoesNotExist:
            return None

    def get_all_stocks_centraux(self) -> List[StockCentral]:
        """Récupère tous les stocks centraux"""
        django_stocks = DjangoStockCentral.objects.all()
        return [
            self._mapper_stock_central_vers_domaine(stock) for stock in django_stocks
        ]

    def get_all_stocks_locaux_by_magasin(
        self, magasin_id: MagasinId
    ) -> List[StockLocal]:
        """Récupère tous les stocks locaux d'un magasin"""
        django_stocks = DjangoStockLocal.objects.filter(magasin_id=str(magasin_id))
        return [self._mapper_stock_local_vers_domaine(stock) for stock in django_stocks]

    def get_all_stocks_locaux(self) -> List[StockLocal]:
        """Récupère tous les stocks locaux de tous les magasins"""
        django_stocks = DjangoStockLocal.objects.all()
        return [self._mapper_stock_local_vers_domaine(stock) for stock in django_stocks]

    def get_stocks_centraux_faibles(self, seuil: int = 10) -> List[StockCentral]:
        """Récupère les stocks centraux sous le seuil spécifié"""
        django_stocks = DjangoStockCentral.objects.filter(quantite__lte=seuil)
        return [
            self._mapper_stock_central_vers_domaine(stock) for stock in django_stocks
        ]

    def get_stocks_locaux_faibles(
        self, magasin_id: MagasinId, seuil: int = 5
    ) -> List[StockLocal]:
        """Récupère les stocks locaux d'un magasin sous le seuil spécifié"""
        django_stocks = DjangoStockLocal.objects.filter(
            magasin_id=str(magasin_id), quantite__lte=seuil
        )
        return [self._mapper_stock_local_vers_domaine(stock) for stock in django_stocks]

    def save_stock_central(self, stock: StockCentral) -> StockCentral:
        """Sauvegarde un stock central (création ou mise à jour)"""
        try:
            # Tentative de mise à jour
            django_stock = DjangoStockCentral.objects.get(
                produit_id=str(stock.produit_id)
            )
            django_stock.quantite = int(stock.quantite)
            django_stock.updated_at = stock.updated_at
            django_stock.save()
        except ObjectDoesNotExist:
            # Création
            django_stock = DjangoStockCentral.objects.create(
                id=str(stock.stock_id),
                produit_id=str(stock.produit_id),
                quantite=int(stock.quantite),
                created_at=stock.created_at,
                updated_at=stock.updated_at,
            )

        return self._mapper_stock_central_vers_domaine(django_stock)

    def save_stock_local(self, stock: StockLocal) -> StockLocal:
        """Sauvegarde un stock local (création ou mise à jour)"""
        try:
            # Tentative de mise à jour
            django_stock = DjangoStockLocal.objects.get(
                produit_id=str(stock.produit_id), magasin_id=str(stock.magasin_id)
            )
            django_stock.quantite = int(stock.quantite)
            django_stock.updated_at = stock.updated_at
            django_stock.save()
        except ObjectDoesNotExist:
            # Création
            django_stock = DjangoStockLocal.objects.create(
                id=str(stock.stock_id),
                produit_id=str(stock.produit_id),
                magasin_id=str(stock.magasin_id),
                quantite=int(stock.quantite),
                created_at=stock.created_at,
                updated_at=stock.updated_at,
            )

        return self._mapper_stock_local_vers_domaine(django_stock)

    def delete_stock_central(self, stock_id: StockId) -> bool:
        """Supprime un stock central"""
        try:
            DjangoStockCentral.objects.get(id=str(stock_id)).delete()
            return True
        except ObjectDoesNotExist:
            return False

    def delete_stock_local(self, stock_id: StockId) -> bool:
        """Supprime un stock local"""
        try:
            DjangoStockLocal.objects.get(id=str(stock_id)).delete()
            return True
        except ObjectDoesNotExist:
            return False

    # Méthodes de mapping

    def _mapper_stock_central_vers_domaine(
        self, django_stock: DjangoStockCentral
    ) -> StockCentral:
        """Convertit un modèle Django StockCentral vers une entité domaine"""
        return StockCentral(
            stock_id=StockId(str(django_stock.id)),
            produit_id=ProduitId(str(django_stock.produit_id)),
            quantite=Quantite.from_int(django_stock.quantite),
            created_at=django_stock.created_at,
            updated_at=django_stock.updated_at,
        )

    def _mapper_stock_local_vers_domaine(
        self, django_stock: DjangoStockLocal
    ) -> StockLocal:
        """Convertit un modèle Django StockLocal vers une entité domaine"""
        return StockLocal(
            stock_id=StockId(str(django_stock.id)),
            produit_id=ProduitId(str(django_stock.produit_id)),
            magasin_id=MagasinId(str(django_stock.magasin_id)),
            quantite=Quantite.from_int(django_stock.quantite),
            created_at=django_stock.created_at,
            updated_at=django_stock.updated_at,
        )
