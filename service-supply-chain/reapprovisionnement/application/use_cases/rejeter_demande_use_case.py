"""
Use Case : Rejeter une demande de réapprovisionnement
Rejet avec validation du motif et règles métier.
"""

from dataclasses import dataclass
from typing import Optional
import logging

from ...domain.entities import DemandeReapprovisionnement, StatutDemande
from ...domain.value_objects import DemandeId, MotifRejet
from ...domain.exceptions import DemandeInvalideError, WorkflowError
from ..repositories.demande_repository import DemandeRepository

logger = logging.getLogger(__name__)


@dataclass
class RejeterDemandeCommand:
    """Commande pour rejeter une demande"""

    demande_id: str
    motif: str


@dataclass
class RejeterDemandeResult:
    """Résultat du rejet d'une demande"""

    succes: bool
    demande_id: str
    message: str
    motif: Optional[str] = None
    details_erreur: Optional[str] = None


class RejeterDemandeUseCase:
    """
    Use Case métier : Rejet d'une demande de réapprovisionnement

    Responsabilités :
    1. Valider les règles métier pour le rejet
    2. Valider le motif de rejet (Value Object)
    3. Appliquer les transitions d'état valides
    4. Mettre à jour le statut via repository
    """

    def __init__(self, demande_repository: DemandeRepository):
        self.demande_repository = demande_repository

    def execute(self, command: RejeterDemandeCommand) -> RejeterDemandeResult:
        """
        Exécute le processus de rejet

        Workflow DDD :
        1. Récupérer la demande (via Repository)
        2. Valider les règles métier (Entité riche)
        3. Créer le motif de rejet (Value Object)
        4. Appliquer le rejet (Entité)
        5. Persister via Repository
        """
        logger.info(f"Début Use Case: Rejeter demande {command.demande_id}")

        try:
            # 1. Récupérer la demande
            demande = self._recuperer_demande(command.demande_id)

            # 2. Créer et valider le motif (Value Object)
            motif_rejet = MotifRejet.from_string(command.motif)

            # 3. Appliquer le rejet (règles métier dans l'entité)
            demande.rejeter(motif_rejet)

            # 4. Persister le changement (rejet direct)
            succes = self.demande_repository.rejeter_demande(demande.demande_id)

            if succes:
                logger.info(f"Use Case réussi: Demande {command.demande_id} rejetée")
                return RejeterDemandeResult(
                    succes=True,
                    demande_id=command.demande_id,
                    message="Demande rejetée avec succès",
                    motif=str(motif_rejet),
                )
            else:
                return RejeterDemandeResult(
                    succes=False,
                    demande_id=command.demande_id,
                    message="Échec de la mise à jour du statut",
                    details_erreur="Erreur lors de la communication avec le service stock",
                )

        except (DemandeInvalideError, WorkflowError, ValueError) as e:
            logger.error(f"Erreur domaine: {e}")
            return RejeterDemandeResult(
                succes=False,
                demande_id=command.demande_id,
                message="Erreur de validation métier",
                details_erreur=str(e),
            )

        except Exception as e:
            logger.error(f"Erreur critique Use Case: {e}")
            return RejeterDemandeResult(
                succes=False,
                demande_id=command.demande_id,
                message="Erreur critique lors du rejet",
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
            produit_id=demande_data["produit_id"],
            magasin_id=demande_data["magasin_id"],
            quantite=demande_data["quantite"],
            statut=StatutDemande(demande_data["statut"]),
            date_creation=demande_data["date_creation"],
        )

        # Validation métier
        if not demande.peut_etre_rejetee():
            raise WorkflowError(
                f"La demande {demande_id} ne peut pas être rejetée (statut: {demande.statut.value})"
            )

        return demande
