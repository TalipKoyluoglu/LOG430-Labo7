"""
Entités du domaine Inventaire
Entités riches avec logique métier pour la gestion des stocks.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .value_objects import ProduitId, MagasinId, Quantite, StockId, DemandeId
from .exceptions import (
    StockInsuffisantError,
    QuantiteInvalideError,
    StockNegatifError,
    InventaireDomainError,
)


class StatutDemandeStock(Enum):
    """États possibles d'une demande de réapprovisionnement"""

    EN_ATTENTE = "En attente"
    APPROUVEE = "Approuvée"
    REFUSEE = "Refusée"


@dataclass
class StockCentral:
    """
    Entité riche représentant le stock central.
    Contient la logique métier de gestion du stock global.
    """

    stock_id: StockId
    produit_id: ProduitId
    quantite: Quantite
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)

    def diminuer(self, quantite_a_diminuer: Quantite) -> None:
        """
        Règle métier : Diminue le stock central avec validation
        """
        if int(quantite_a_diminuer) > int(self.quantite):
            raise StockInsuffisantError(
                f"Stock central insuffisant pour le produit {self.produit_id}. "
                f"Disponible: {self.quantite}, Demandé: {quantite_a_diminuer}"
            )

        nouvelle_quantite = int(self.quantite) - int(quantite_a_diminuer)
        self.quantite = Quantite.from_int(nouvelle_quantite)
        self.updated_at = datetime.now()

    def augmenter(self, quantite_a_ajouter: Quantite) -> None:
        """
        Règle métier : Augmente le stock central (réception, rollback)
        """
        nouvelle_quantite = int(self.quantite) + int(quantite_a_ajouter)
        self.quantite = Quantite.from_int(nouvelle_quantite)
        self.updated_at = datetime.now()

    def peut_satisfaire_demande(self, quantite_demandee: Quantite) -> bool:
        """
        Règle métier : Vérifie si le stock peut satisfaire une demande
        """
        return int(self.quantite) >= int(quantite_demandee)

    def est_stock_faible(self, seuil: int = 10) -> bool:
        """
        Règle métier : Détermine si le stock est faible
        """
        return int(self.quantite) <= seuil

    def est_stock_critique(self, seuil: int = 5) -> bool:
        """
        Règle métier : Détermine si le stock est critique
        """
        return int(self.quantite) <= seuil


@dataclass
class StockLocal:
    """
    Entité riche représentant le stock local d'un magasin.
    Contient la logique métier de gestion du stock local.
    """

    stock_id: StockId
    produit_id: ProduitId
    magasin_id: MagasinId
    quantite: Quantite
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)

    def diminuer(self, quantite_a_diminuer: Quantite) -> None:
        """
        Règle métier : Diminue le stock local (ventes, transferts)
        """
        if int(quantite_a_diminuer) > int(self.quantite):
            raise StockInsuffisantError(
                f"Stock local insuffisant pour le produit {self.produit_id} "
                f"au magasin {self.magasin_id}. "
                f"Disponible: {self.quantite}, Demandé: {quantite_a_diminuer}"
            )

        nouvelle_quantite = int(self.quantite) - int(quantite_a_diminuer)
        self.quantite = Quantite.from_int(nouvelle_quantite)
        self.updated_at = datetime.now()

    def augmenter(self, quantite_a_ajouter: Quantite) -> None:
        """
        Règle métier : Augmente le stock local (réapprovisionnement)
        """
        nouvelle_quantite = int(self.quantite) + int(quantite_a_ajouter)
        self.quantite = Quantite.from_int(nouvelle_quantite)
        self.updated_at = datetime.now()

    def peut_satisfaire_vente(self, quantite_vendue: Quantite) -> bool:
        """
        Règle métier : Vérifie si le stock local peut satisfaire une vente
        """
        return int(self.quantite) >= int(quantite_vendue)

    def necessite_reapprovisionnement(self, seuil: int = 5) -> bool:
        """
        Règle métier : Détermine si le magasin a besoin de réapprovisionnement
        """
        return int(self.quantite) <= seuil

    def get_niveau_stock(self) -> str:
        """
        Règle métier : Retourne le niveau de stock (Haut/Moyen/Bas/Critique)
        """
        quantite = int(self.quantite)
        if quantite <= 2:
            return "Critique"
        elif quantite <= 5:
            return "Bas"
        elif quantite <= 20:
            return "Moyen"
        else:
            return "Haut"


@dataclass
class DemandeReapprovisionnement:
    """
    Entité riche représentant une demande de réapprovisionnement.
    Contient la logique métier du workflow de demande.
    """

    demande_id: DemandeId
    produit_id: ProduitId
    magasin_id: MagasinId
    quantite: Quantite
    statut: StatutDemandeStock
    date_creation: datetime
    date_modification: Optional[datetime] = None

    def peut_etre_approuvee(self) -> bool:
        """
        Règle métier : Une demande ne peut être approuvée que si elle est en attente
        """
        return self.statut == StatutDemandeStock.EN_ATTENTE

    def peut_etre_rejetee(self) -> bool:
        """
        Règle métier : Une demande ne peut être rejetée que si elle est en attente
        """
        return self.statut == StatutDemandeStock.EN_ATTENTE

    def approuver(self) -> None:
        """
        Règle métier : Approuve la demande si possible
        """
        if not self.peut_etre_approuvee():
            raise InventaireDomainError(
                f"Impossible d'approuver une demande avec le statut {self.statut.value}"
            )

        self.statut = StatutDemandeStock.APPROUVEE
        self.date_modification = datetime.now()

    def rejeter(self) -> None:
        """
        Règle métier : Rejette la demande si possible
        """
        if not self.peut_etre_rejetee():
            raise InventaireDomainError(
                f"Impossible de rejeter une demande avec le statut {self.statut.value}"
            )

        self.statut = StatutDemandeStock.REFUSEE
        self.date_modification = datetime.now()

    def est_ancienne(self, jours: int = 7) -> bool:
        """
        Règle métier : Détermine si la demande est ancienne
        """
        delta = datetime.now() - self.date_creation
        return delta.days >= jours

    def est_terminee(self) -> bool:
        """
        Règle métier : Vérifie si la demande est dans un état final
        """
        return self.statut in [StatutDemandeStock.APPROUVEE, StatutDemandeStock.REFUSEE]


@dataclass
class TransfertStock:
    """
    Entité représentant un transfert de stock central vers local.
    Orchestration du mouvement de stock avec validation métier.
    """

    stock_central: StockCentral
    stock_local: StockLocal
    quantite_transfert: Quantite

    def valider_transfert(self) -> bool:
        """
        Règle métier : Valide si le transfert est possible
        """
        return self.stock_central.peut_satisfaire_demande(self.quantite_transfert)

    def executer_transfert(self) -> None:
        """
        Règle métier : Exécute le transfert avec validation atomique
        """
        if not self.valider_transfert():
            raise StockInsuffisantError(
                f"Transfert impossible : stock central insuffisant"
            )

        # Transfert atomique
        self.stock_central.diminuer(self.quantite_transfert)
        self.stock_local.augmenter(self.quantite_transfert)


@dataclass
class InventaireMagasin:
    """
    Agrégat représentant l'inventaire complet d'un magasin.
    Contient la logique métier de gestion globale du magasin.
    """

    magasin_id: MagasinId
    stocks_locaux: List[StockLocal] = field(default_factory=list)

    def ajouter_stock(self, stock: StockLocal) -> None:
        """
        Ajoute un stock local à l'inventaire du magasin
        """
        if stock.magasin_id != self.magasin_id:
            raise InventaireDomainError(
                f"Stock appartient au magasin {stock.magasin_id}, pas à {self.magasin_id}"
            )
        self.stocks_locaux.append(stock)

    def get_stock_produit(self, produit_id: ProduitId) -> Optional[StockLocal]:
        """
        Récupère le stock d'un produit spécifique
        """
        for stock in self.stocks_locaux:
            if stock.produit_id == produit_id:
                return stock
        return None

    def get_stocks_faibles(self, seuil: int = 5) -> List[StockLocal]:
        """
        Règle métier : Retourne tous les stocks nécessitant un réapprovisionnement
        """
        return [
            stock
            for stock in self.stocks_locaux
            if stock.necessite_reapprovisionnement(seuil)
        ]

    def get_valeur_totale_inventaire(self) -> int:
        """
        Règle métier : Calcule la quantité totale de l'inventaire
        """
        return sum(int(stock.quantite) for stock in self.stocks_locaux)

    def get_nombre_produits_differents(self) -> int:
        """
        Règle métier : Nombre de produits différents en stock
        """
        return len(self.stocks_locaux)
