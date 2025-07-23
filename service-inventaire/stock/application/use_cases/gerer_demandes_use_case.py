"""
Use Case pour la gestion des demandes de réapprovisionnement
Contient toute la logique métier pour les opérations sur les demandes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

from ..repositories.stock_repository import StockRepository
from ..repositories.demande_repository import DemandeRepository
from ..services.produit_service import ProduitService
from ..services.magasin_service import MagasinService

from ...domain.entities import DemandeReapprovisionnement, StatutDemandeStock
from ...domain.value_objects import ProduitId, MagasinId, Quantite, DemandeId
from ...domain.exceptions import (
    InventaireDomainError,
    ProduitInexistantError,
    MagasinInexistantError,
)


@dataclass
class CreerDemandeRequest:
    """DTO pour les demandes de création de demande de réapprovisionnement"""

    produit_id: str
    magasin_id: str
    quantite: int


@dataclass
class DemandeResponse:
    """DTO pour la réponse des demandes de réapprovisionnement"""

    id: str
    produit_id: str
    magasin_id: str
    quantite: int
    statut: str
    date_creation: str
    date_modification: str = None
    nom_produit: str = None
    nom_magasin: str = None


class GererDemandesUseCase:
    """
    Use Case pour toutes les opérations de gestion des demandes de réapprovisionnement.
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

    def creer_demande(self, request: CreerDemandeRequest) -> DemandeResponse:
        """
        Règle métier : Crée une nouvelle demande de réapprovisionnement
        Fonctionnalité équivalente à l'API POST /demandes/
        """
        produit_id = ProduitId(request.produit_id)
        magasin_id = MagasinId(request.magasin_id)
        quantite = Quantite.from_int(request.quantite)

        # Validation métier
        self.produit_service.valider_produit_existe(produit_id)
        self.magasin_service.valider_magasin_existe(magasin_id)

        # Règle métier : Vérifier que le stock central est suffisant
        stock_central = self.stock_repository.get_stock_central_by_produit(produit_id)
        if stock_central is None:
            raise InventaireDomainError(
                f"Aucun stock central disponible pour le produit {produit_id}"
            )
        if stock_central.quantite < quantite:
            raise InventaireDomainError(
                f"Stock central insuffisant pour le produit {produit_id}. "
                f"Disponible: {stock_central.quantite}, Demandé: {quantite}"
            )

        # Règle métier : Pas de demande en doublon
        if self.demande_repository.exists_demande_en_attente(produit_id, magasin_id):
            raise InventaireDomainError(
                f"Une demande est déjà en attente pour le produit {produit_id} "
                f"au magasin {magasin_id}"
            )

        # Créer la demande
        demande = DemandeReapprovisionnement(
            demande_id=DemandeId.generate(),
            produit_id=produit_id,
            magasin_id=magasin_id,
            quantite=quantite,
            statut=StatutDemandeStock.EN_ATTENTE,
            date_creation=datetime.now(),
        )

        demande_sauvee = self.demande_repository.save(demande)

        return self._mapper_vers_response(demande_sauvee)

    def lister_demandes_en_attente(self) -> List[DemandeResponse]:
        """
        Règle métier : Liste toutes les demandes en attente de traitement
        Fonctionnalité équivalente à l'API GET /demandes/en-attente/
        """
        demandes = self.demande_repository.get_demandes_en_attente()
        return [self._mapper_vers_response(demande) for demande in demandes]

    def lister_demandes_par_magasin(self, magasin_id: int) -> List[DemandeResponse]:
        """
        Règle métier : Liste toutes les demandes d'un magasin spécifique
        Fonctionnalité équivalente à l'API GET /demandes/magasin/{id}/
        """
        magasin_id_vo = MagasinId(magasin_id)
        self.magasin_service.valider_magasin_existe(magasin_id_vo)

        demandes = self.demande_repository.get_demandes_by_magasin(magasin_id_vo)
        return [self._mapper_vers_response(demande) for demande in demandes]

    def lister_demandes_par_produit(self, produit_id: int) -> List[DemandeResponse]:
        """
        Règle métier : Liste toutes les demandes pour un produit spécifique
        Fonctionnalité équivalente à l'API GET /demandes/produit/{id}/
        """
        produit_id_vo = ProduitId(produit_id)
        self.produit_service.valider_produit_existe(produit_id_vo)

        demandes = self.demande_repository.get_demandes_by_produit(produit_id_vo)
        return [self._mapper_vers_response(demande) for demande in demandes]

    def lister_demandes_par_statut(self, statut: str) -> List[DemandeResponse]:
        """
        Règle métier : Liste toutes les demandes avec un statut spécifique
        Fonctionnalité équivalente à l'API GET /demandes/statut/{statut}/
        """
        try:
            statut_enum = StatutDemandeStock(statut)
        except ValueError:
            raise InventaireDomainError(f"Statut '{statut}' invalide")

        demandes = self.demande_repository.get_demandes_by_statut(statut_enum)
        return [self._mapper_vers_response(demande) for demande in demandes]

    def supprimer_demande(self, demande_id: str) -> Dict[str, Any]:
        """
        Règle métier : Supprime une demande (seulement si en attente)
        Fonctionnalité équivalente à l'API DELETE /demandes/{id}/
        """
        demande_id_vo = DemandeId(demande_id)

        demande = self.demande_repository.get_by_id(demande_id_vo)
        if demande is None:
            raise InventaireDomainError(f"Demande {demande_id} introuvable")

        # Règle métier : Ne peut supprimer que les demandes en attente
        if demande.statut != StatutDemandeStock.EN_ATTENTE:
            raise InventaireDomainError(
                f"Impossible de supprimer une demande avec le statut '{demande.statut.value}'"
            )

        success = self.demande_repository.delete(demande_id_vo)

        return {
            "success": success,
            "message": f"Demande {demande_id} supprimée avec succès",
        }

    def analyser_besoins_reapprovisionnement(self, magasin_id: int) -> Dict[str, Any]:
        """
        Règle métier : Analyse les besoins de réapprovisionnement d'un magasin
        Nouvelle fonctionnalité métier pour identifier les produits à faible stock
        """
        magasin_id_vo = MagasinId(magasin_id)
        self.magasin_service.valider_magasin_existe(magasin_id_vo)

        # Récupérer les stocks faibles du magasin
        stocks_faibles = self.stock_repository.get_stocks_locaux_faibles(
            magasin_id_vo, seuil=5
        )

        # Vérifier lesquels ont déjà une demande en attente
        produits_sans_demande = []
        for stock in stocks_faibles:
            if not self.demande_repository.exists_demande_en_attente(
                stock.produit_id, magasin_id_vo
            ):
                produits_sans_demande.append(
                    {
                        "produit_id": int(stock.produit_id),
                        "quantite_actuelle": int(stock.quantite),
                        "niveau": stock.get_niveau_stock(),
                        "quantite_suggeree": max(
                            10 - int(stock.quantite), 5
                        ),  # Règle métier
                        "nom_produit": self.produit_service.get_nom_produit(
                            stock.produit_id
                        ),
                    }
                )

        return {
            "magasin_id": magasin_id,
            "nom_magasin": self.magasin_service.get_nom_magasin(magasin_id_vo),
            "total_stocks_faibles": len(stocks_faibles),
            "produits_sans_demande": produits_sans_demande,
            "recommandation": (
                "Créer des demandes pour les produits listés"
                if produits_sans_demande
                else "Aucune action requise"
            ),
        }

    def obtenir_demande_par_id(self, demande_id: str) -> DemandeResponse:
        """
        Règle métier : Récupère une demande spécifique par son ID
        Fonctionnalité équivalente à l'API GET /demandes/{id}/
        """
        demande_id_vo = DemandeId(demande_id)

        demande = self.demande_repository.get_by_id(demande_id_vo)
        if demande is None:
            raise InventaireDomainError(f"Demande {demande_id} introuvable")

        return self._mapper_vers_response(demande)

    def approuver_demande(self, demande_id: str) -> DemandeResponse:
        """
        Règle métier : Approuve une demande de réapprovisionnement
        ET effectue le transfert de stock central vers stock local
        """
        demande_id_vo = DemandeId(demande_id)

        demande = self.demande_repository.get_by_id(demande_id_vo)
        if demande is None:
            raise InventaireDomainError(f"Demande {demande_id} introuvable")

        # Vérification du stock central disponible
        stock_central = self.stock_repository.get_stock_central_by_produit(
            demande.produit_id
        )
        if stock_central is None or stock_central.quantite < demande.quantite:
            raise InventaireDomainError(
                f"Stock central insuffisant pour approuver la demande. "
                f"Disponible: {stock_central.quantite if stock_central else 0}, "
                f"Demandé: {demande.quantite}"
            )

        # 1. Approuver la demande (changement de statut)
        demande.approuver()

        # 2. TRANSFERT DE STOCK : Central → Local
        # Diminuer stock central
        stock_central.diminuer(demande.quantite)
        self.stock_repository.save_stock_central(stock_central)

        # Augmenter stock local (ou créer si n'existe pas)
        stock_local = self.stock_repository.get_stock_local_by_produit_magasin(
            demande.produit_id, demande.magasin_id
        )
        if stock_local is None:
            # Créer nouveau stock local
            from ...domain.entities import StockLocal
            from ...domain.value_objects import StockId

            stock_local = StockLocal(
                stock_id=StockId.generate(),
                produit_id=demande.produit_id,
                magasin_id=demande.magasin_id,
                quantite=demande.quantite,
                created_at=datetime.now(),
            )
        else:
            # Augmenter stock existant
            stock_local.augmenter(demande.quantite)

        self.stock_repository.save_stock_local(stock_local)

        # 3. Sauvegarder la demande approuvée
        demande_sauvee = self.demande_repository.save(demande)

        return self._mapper_vers_response(demande_sauvee)

    def rejeter_demande(self, demande_id: str) -> DemandeResponse:
        """
        Règle métier : Rejette une demande de réapprovisionnement
        Nouveau Use Case pour l'architecture supply chain
        """
        demande_id_vo = DemandeId(demande_id)

        demande = self.demande_repository.get_by_id(demande_id_vo)
        if demande is None:
            raise InventaireDomainError(f"Demande {demande_id} introuvable")

        # Utilise la logique métier de l'entité
        demande.rejeter()

        # Sauvegarde
        demande_sauvee = self.demande_repository.save(demande)

        return self._mapper_vers_response(demande_sauvee)

    # Méthodes privées

    def _mapper_vers_response(
        self, demande: DemandeReapprovisionnement
    ) -> DemandeResponse:
        """Mappe une entité Demande vers un DTO de réponse"""
        try:
            nom_produit = self.produit_service.get_nom_produit(demande.produit_id)
        except:
            nom_produit = f"Produit {demande.produit_id}"

        try:
            nom_magasin = self.magasin_service.get_nom_magasin(demande.magasin_id)
        except:
            nom_magasin = f"Magasin {demande.magasin_id}"

        return DemandeResponse(
            id=str(demande.demande_id),
            produit_id=str(demande.produit_id),
            magasin_id=str(demande.magasin_id),
            quantite=int(demande.quantite),
            statut=demande.statut.value,
            date_creation=demande.date_creation.isoformat(),
            date_modification=(
                demande.date_modification.isoformat()
                if demande.date_modification
                else None
            ),
            nom_produit=nom_produit,
            nom_magasin=nom_magasin,
        )
