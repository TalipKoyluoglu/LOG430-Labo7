"""
Use Case: Annuler une Vente
Fonctionnalité métier complète pour annuler une vente existante
"""

from typing import Dict, Any

from ..repositories.vente_repository import VenteRepository
from ..services.stock_service import StockService
from ...domain.exceptions import VenteInvalideError


class AnnulerVenteUseCase:
    """
    Use Case: Annuler une vente existante

    Orchestration complète de la fonctionnalité métier:
    1. Récupération de la vente
    2. Validation de l'état
    3. Annulation (logique métier dans l'entité)
    4. Restauration du stock
    5. Persistance
    """

    def __init__(self, vente_repository: VenteRepository, stock_service: StockService):
        self._vente_repo = vente_repository
        self._stock_service = stock_service

    def execute(self, vente_id: str, motif: str) -> Dict[str, Any]:
        """
        Exécute le cas d'usage d'annulation de vente

        Args:
            vente_id: ID de la vente à annuler
            motif: Motif de l'annulation

        Returns:
            Dict contenant le résultat de l'annulation

        Raises:
            VenteInvalideError: Si la vente n'existe pas
            VenteDejaAnnuleeError: Si la vente est déjà annulée
        """

        # 1. Récupération de la vente
        vente = self._vente_repo.get_by_id(vente_id)
        if not vente:
            raise VenteInvalideError(f"Vente {vente_id} non trouvée")

        # 2. Obtenir les quantités avant annulation (pour restauration stock)
        quantites_par_produit = vente.obtenir_quantites_par_produit()
        magasin_id = vente.magasin_id

        # 3. Annulation (logique métier protégée dans l'entité)
        vente.annuler(motif)

        # 4. Restauration du stock (effet de bord)
        for produit_id, quantite in quantites_par_produit.items():
            self._stock_service.increase_stock(magasin_id, produit_id, quantite)

        # 5. Persistance de la vente annulée
        self._vente_repo.save(vente)

        # 6. Retour du résultat
        return {
            "success": True,
            "message": "Vente annulée avec succès",
            "vente_id": str(vente.id),
            "statut": vente.statut.value,
            "date_annulation": vente.date_annulation.isoformat(),
            "motif": vente.motif_annulation,
        }
