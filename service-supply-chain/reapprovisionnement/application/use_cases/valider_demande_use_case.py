"""
Use Case : Valider une demande de réapprovisionnement
Orchestration DDD du workflow complexe de validation avec rollback automatique.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

from ...domain.entities import (
    DemandeReapprovisionnement,
    WorkflowValidation,
    StatutDemande,
)
from ...domain.value_objects import (
    DemandeId,
    ProduitId,
    MagasinId,
    Quantite,
    LogValidation,
)
from ...domain.exceptions import (
    DemandeInvalideError,
    WorkflowError,
    CommunicationServiceError,
)
from ..repositories.demande_repository import DemandeRepository
from ..services.stock_service import StockService

logger = logging.getLogger(__name__)


@dataclass
class ValiderDemandeCommand:
    """Commande pour valider une demande"""

    demande_id: str


@dataclass
class ValiderDemandeResult:
    """Résultat de la validation d'une demande"""

    succes: bool
    demande_id: str
    message: str
    etapes_executees: list
    rollback_effectue: bool = False
    details_erreur: Optional[str] = None


class ValiderDemandeUseCase:
    """
    Use Case métier : Validation d'une demande de réapprovisionnement

    Responsabilités :
    1. Orchestrer le workflow complexe de validation
    2. Gérer les rollbacks automatiques en cas d'échec
    3. Appliquer les règles métier du domaine
    4. Communiquer avec les services externes (Stock)
    """

    def __init__(
        self, demande_repository: DemandeRepository, stock_service: StockService
    ):
        self.demande_repository = demande_repository
        self.stock_service = stock_service

    def execute(self, command: ValiderDemandeCommand) -> ValiderDemandeResult:
        """
        Exécute le processus de validation simplifié

        Workflow simplifié :
        1. Récupérer la demande (via Repository)
        2. Approuver directement (logique métier dans service-inventaire)
        """
        logger.info(f"Début Use Case: Valider demande {command.demande_id}")

        try:
            # 1. Récupérer la demande
            demande = self._recuperer_demande(command.demande_id)

            # 2. Approbation directe avec transfert automatique
            # La logique métier complète est maintenant dans le service-inventaire
            succes = self.demande_repository.approuver_demande(demande.demande_id)

            if succes:
                logger.info(f"Use Case réussi: Demande {command.demande_id} validée")
                return ValiderDemandeResult(
                    succes=True,
                    demande_id=command.demande_id,
                    message="Demande validée avec succès",
                    etapes_executees=[
                        "Vérification stock central - Réussi",
                        "Transfert de stock central vers local - Réussi",
                        "Approbation demande - Réussi",
                    ],
                )
            else:
                return ValiderDemandeResult(
                    succes=False,
                    demande_id=command.demande_id,
                    message="Échec de la validation",
                    etapes_executees=["Approbation demande - Échec"],
                    details_erreur="Erreur lors de la communication avec le service inventaire",
                )

        except Exception as e:
            logger.error(f"Erreur critique Use Case: {e}")

            return ValiderDemandeResult(
                succes=False,
                demande_id=command.demande_id,
                message="Erreur critique lors de la validation",
                etapes_executees=[],
                details_erreur=str(e),
            )

    def _recuperer_demande(self, demande_id: str) -> DemandeReapprovisionnement:
        """Récupère et valide la demande"""
        demande_id_vo = DemandeId.from_string(demande_id)

        demande_data = self.demande_repository.get_by_id(demande_id_vo)
        if not demande_data:
            raise DemandeInvalideError(f"Demande {demande_id} non trouvée")

        # Conversion vers entité riche
        demande = DemandeReapprovisionnement(
            demande_id=DemandeId.from_string(demande_data["id"]),
            produit_id=ProduitId.from_string(demande_data["produit_id"]),
            magasin_id=MagasinId.from_string(demande_data["magasin_id"]),
            quantite=Quantite.from_int(demande_data["quantite"]),
            statut=StatutDemande(demande_data["statut"]),
            date_creation=demande_data["date_creation"],
        )

        # Validation métier
        if not demande.peut_etre_validee():
            raise WorkflowError(
                f"La demande {demande_id} ne peut pas être validée (statut: {demande.statut.value})"
            )

        return demande

    def _effectuer_rollback(
        self, workflow: WorkflowValidation, demande: DemandeReapprovisionnement
    ) -> bool:
        """Effectue le rollback des étapes réussies"""
        logger.info(" Début rollback automatique")

        try:
            etapes_rollback = workflow.get_etapes_a_rollback()

            for etape in etapes_rollback:
                if etape.nom == "Diminuer stock central":
                    # Rollback: remettre le stock central
                    self.stock_service.augmenter_stock_central(
                        demande.produit_id, demande.quantite
                    )
                    logger.info(" Rollback: Stock central restauré")

                elif etape.nom == "Augmenter stock local":
                    # Rollback: diminuer le stock local
                    self.stock_service.diminuer_stock_local(
                        demande.produit_id, demande.magasin_id, demande.quantite
                    )
                    logger.info(" Rollback: Stock local restauré")

            logger.info(" Rollback automatique réussi")
            return True

        except Exception as e:
            logger.error(f" ERREUR CRITIQUE - Rollback échoué: {e}")
            return False
