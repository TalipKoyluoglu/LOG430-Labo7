"""
Entités du domaine Ventes
Les entités contiennent l'identité et la logique métier
"""

import uuid
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from .value_objects import StatutVente, LigneVenteVO, ProduitId, MagasinId, ClientId
from .exceptions import VenteDejaAnnuleeError, StockInsuffisantError


class Vente:
    """
    Entité Aggregate Root - Vente
    Contient toute la logique métier liée aux ventes
    """

    def __init__(
        self,
        id: uuid.UUID,
        magasin_id: MagasinId,
        client_id: Optional[ClientId] = None,
        date_vente: Optional[datetime] = None,
    ):
        self._id = id
        self._magasin_id = magasin_id
        self._client_id = client_id
        self._date_vente = date_vente or datetime.now()
        self._lignes: List[LigneVenteVO] = []
        self._statut = StatutVente.ACTIVE
        self._date_annulation: Optional[datetime] = None
        self._motif_annulation: Optional[str] = None

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def magasin_id(self) -> MagasinId:
        return self._magasin_id

    @property
    def client_id(self) -> Optional[ClientId]:
        return self._client_id

    @property
    def date_vente(self) -> datetime:
        return self._date_vente

    @property
    def lignes(self) -> List[LigneVenteVO]:
        return self._lignes.copy()

    @property
    def statut(self) -> StatutVente:
        return self._statut

    @property
    def date_annulation(self) -> Optional[datetime]:
        return self._date_annulation

    @property
    def motif_annulation(self) -> Optional[str]:
        return self._motif_annulation

    def ajouter_ligne(
        self, produit_id: ProduitId, quantite: int, prix_unitaire: Decimal
    ) -> None:
        """
        Ajoute une ligne de vente (logique métier dans l'entité)
        """
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

        if prix_unitaire <= 0:
            raise ValueError("Le prix unitaire doit être positif")

        ligne = LigneVenteVO(
            id=uuid.uuid4(),
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
        )
        self._lignes.append(ligne)

    def calculer_total(self) -> Decimal:
        """
        Calcule le total de la vente (logique métier)
        """
        return sum(ligne.sous_total for ligne in self._lignes)

    def annuler(self, motif: str) -> None:
        """
        Annule la vente (logique métier avec invariants)
        """
        if self._statut != StatutVente.ACTIVE:
            raise VenteDejaAnnuleeError(f"La vente est déjà {self._statut.value}")

        if not motif.strip():
            raise ValueError("Un motif d'annulation est requis")

        self._statut = StatutVente.ANNULEE
        self._date_annulation = datetime.now()
        self._motif_annulation = motif

    def rembourser(self, motif: str) -> None:
        """
        Marque la vente comme remboursée
        """
        if self._statut == StatutVente.ACTIVE:
            # Annuler d'abord puis rembourser
            self.annuler(motif)

        self._statut = StatutVente.REMBOURSEE

    def est_active(self) -> bool:
        """
        Vérifie si la vente est active (logique métier)
        """
        return self._statut == StatutVente.ACTIVE

    def est_annulee(self) -> bool:
        """
        Vérifie si la vente est annulée
        """
        return self._statut in [StatutVente.ANNULEE, StatutVente.REMBOURSEE]

    def obtenir_produits_vendus(self) -> List[ProduitId]:
        """
        Retourne la liste des produits vendus (pour restauration stock)
        """
        return [ligne.produit_id for ligne in self._lignes]

    def obtenir_quantites_par_produit(self) -> dict:
        """
        Retourne un dictionnaire {produit_id: quantite} pour restauration stock
        """
        return {ligne.produit_id: ligne.quantite for ligne in self._lignes}


class Magasin:
    """
    Entité Magasin avec logique métier
    """

    def __init__(self, id: MagasinId, nom: str, adresse: str):
        self._id = id
        self._nom = nom
        self._adresse = adresse

    @property
    def id(self) -> MagasinId:
        return self._id

    @property
    def nom(self) -> str:
        return self._nom

    @property
    def adresse(self) -> str:
        return self._adresse

    def peut_vendre(
        self, produit_id: ProduitId, quantite: int, stock_disponible: int
    ) -> bool:
        """
        Logique métier : vérifie si le magasin peut effectuer une vente
        """
        return stock_disponible >= quantite

    def __str__(self):
        return self._nom


class CommandeEcommerce:
    """
    Entité pour les commandes e-commerce
    Étend le concept de Vente avec le workflow e-commerce
    """

    def __init__(
        self,
        id: uuid.UUID,
        client_id: ClientId,
        date_commande: Optional[datetime] = None,
    ):
        self._id = id
        self._client_id = client_id
        self._date_commande = date_commande or datetime.now()
        self._lignes: List[LigneVenteVO] = []
        self._statut = StatutCommande.EN_ATTENTE
        self._adresse_livraison: Optional[str] = None
        self._mode_paiement: Optional[str] = None
        self._date_paiement: Optional[datetime] = None
        self._date_livraison: Optional[datetime] = None
        self._frais_livraison: Decimal = Decimal("0.00")
        self._notes_commande: Optional[str] = None

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def client_id(self) -> ClientId:
        return self._client_id

    @property
    def date_commande(self) -> datetime:
        return self._date_commande

    @property
    def lignes(self) -> List[LigneVenteVO]:
        return self._lignes.copy()

    @property
    def statut(self) -> "StatutCommande":
        return self._statut

    @property
    def adresse_livraison(self) -> Optional[str]:
        return self._adresse_livraison

    @property
    def frais_livraison(self) -> Decimal:
        return self._frais_livraison

    def ajouter_ligne(
        self, produit_id: ProduitId, quantite: int, prix_unitaire: Decimal
    ) -> None:
        """
        Ajoute une ligne de commande (réutilise la logique métier de Vente)
        """
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

        if prix_unitaire <= 0:
            raise ValueError("Le prix unitaire doit être positif")

        ligne = LigneVenteVO(
            id=uuid.uuid4(),
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
        )
        self._lignes.append(ligne)

    def calculer_sous_total(self) -> Decimal:
        """
        Calcule le sous-total (produits uniquement)
        """
        return sum(ligne.sous_total for ligne in self._lignes)

    def calculer_total(self) -> Decimal:
        """
        Calcule le total avec frais de livraison
        """
        return self.calculer_sous_total() + self._frais_livraison

    def definir_adresse_livraison(self, adresse: str) -> None:
        """
        Définit l'adresse de livraison
        """
        if not adresse.strip():
            raise ValueError("L'adresse de livraison est requise")
        self._adresse_livraison = adresse

    def calculer_frais_livraison(self, distance_km: float = None) -> None:
        """
        Calcule les frais de livraison selon la logique métier
        """
        # Logique métier pour les frais de livraison
        sous_total = self.calculer_sous_total()

        if sous_total >= Decimal("100.00"):
            # Livraison gratuite si commande > 100€
            self._frais_livraison = Decimal("0.00")
        elif distance_km and distance_km > 10:
            # Livraison longue distance
            self._frais_livraison = Decimal("15.00")
        else:
            # Livraison standard
            self._frais_livraison = Decimal("7.50")

    def valider_commande(self) -> None:
        """
        Valide la commande (transition vers VALIDEE)
        """
        if not self._lignes:
            raise ValueError("Impossible de valider une commande vide")

        if not self._adresse_livraison:
            raise ValueError("L'adresse de livraison est requise")

        if self._statut != StatutCommande.EN_ATTENTE:
            raise ValueError(
                f"Impossible de valider une commande en statut {self._statut.value}"
            )

        self._statut = StatutCommande.VALIDEE

    def confirmer_paiement(self, mode_paiement: str) -> None:
        """
        Confirme le paiement de la commande
        """
        if self._statut != StatutCommande.VALIDEE:
            raise ValueError("La commande doit être validée avant le paiement")

        self._mode_paiement = mode_paiement
        self._date_paiement = datetime.now()
        self._statut = StatutCommande.PAYEE

    def expedier_commande(self) -> None:
        """
        Marque la commande comme expédiée
        """
        if self._statut != StatutCommande.PAYEE:
            raise ValueError("La commande doit être payée avant expédition")

        self._statut = StatutCommande.EXPEDIEE

    def livrer_commande(self) -> None:
        """
        Marque la commande comme livrée
        """
        if self._statut != StatutCommande.EXPEDIEE:
            raise ValueError("La commande doit être expédiée avant livraison")

        self._date_livraison = datetime.now()
        self._statut = StatutCommande.LIVREE

    def annuler_commande(self, motif: str) -> None:
        """
        Annule la commande e-commerce
        """
        if self._statut in [StatutCommande.EXPEDIEE, StatutCommande.LIVREE]:
            raise ValueError("Impossible d'annuler une commande expédiée ou livrée")

        if not motif.strip():
            raise ValueError("Un motif d'annulation est requis")

        self._statut = StatutCommande.ANNULEE
        self._notes_commande = f"Annulée: {motif}"

    def est_modifiable(self) -> bool:
        """
        Vérifie si la commande peut encore être modifiée
        """
        return self._statut == StatutCommande.EN_ATTENTE

    def obtenir_produits_commandes(self) -> List[ProduitId]:
        """
        Retourne la liste des produits commandés
        """
        return [ligne.produit_id for ligne in self._lignes]

    def obtenir_quantites_par_produit(self) -> dict:
        """
        Retourne un dictionnaire {produit_id: quantite}
        """
        return {ligne.produit_id: ligne.quantite for ligne in self._lignes}
