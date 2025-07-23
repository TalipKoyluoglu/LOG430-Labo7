"""
Entités du domaine Réapprovisionnement
Les entités contiennent la logique métier et les invariants du domaine.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .value_objects import (
    DemandeId,
    ProduitId,
    MagasinId,
    Quantite,
    MotifRejet,
    LogValidation,
)
from .exceptions import (
    DemandeInvalideError,
    EtapeValidationError,
    RollbackError,
    WorkflowError,
)


class StatutDemande(Enum):
    """États possibles d'une demande de réapprovisionnement"""

    EN_ATTENTE = "En attente"
    APPROUVEE = "Approuvée"
    REFUSEE = "Refusée"
    EN_COURS_VALIDATION = "En cours de validation"
    ECHEC_VALIDATION = "Échec validation"


@dataclass
class DemandeReapprovisionnement:
    """
    Entité riche représentant une demande de réapprovisionnement.
    Contient toute la logique métier du workflow d'approbation.
    """

    demande_id: DemandeId
    produit_id: ProduitId
    magasin_id: MagasinId
    quantite: Quantite
    statut: StatutDemande
    date_creation: datetime
    date_validation: Optional[datetime] = None
    motif_rejet: Optional[MotifRejet] = None
    log_validation: List[LogValidation] = field(default_factory=list)

    def peut_etre_validee(self) -> bool:
        """Règle métier : Une demande ne peut être validée que si elle est en attente"""
        return self.statut == StatutDemande.EN_ATTENTE

    def peut_etre_rejetee(self) -> bool:
        """Règle métier : Une demande ne peut être rejetée que si elle est en attente"""
        return self.statut == StatutDemande.EN_ATTENTE

    def demarrer_validation(self) -> None:
        """Démarre le processus de validation"""
        if not self.peut_etre_validee():
            raise WorkflowError(
                f"Impossible de valider une demande avec le statut {self.statut.value}"
            )

        self.statut = StatutDemande.EN_COURS_VALIDATION
        self._ajouter_log("Début du processus de validation")

    def marquer_approuvee(self) -> None:
        """Marque la demande comme approuvée (succès complet)"""
        if self.statut != StatutDemande.EN_COURS_VALIDATION:
            raise WorkflowError("La validation doit être en cours pour approuver")

        self.statut = StatutDemande.APPROUVEE
        self.date_validation = datetime.now()
        self._ajouter_log("Demande approuvée avec succès")

    def marquer_echec_validation(self, erreur: str) -> None:
        """Marque la demande en échec de validation (rollback nécessaire)"""
        if self.statut != StatutDemande.EN_COURS_VALIDATION:
            raise WorkflowError(
                "La validation doit être en cours pour marquer un échec"
            )

        self.statut = StatutDemande.ECHEC_VALIDATION
        self._ajouter_log(f"Échec de validation: {erreur}")

    def rejeter(self, motif: MotifRejet) -> None:
        """Rejette la demande avec un motif"""
        if not self.peut_etre_rejetee():
            raise WorkflowError(
                f"Impossible de rejeter une demande avec le statut {self.statut.value}"
            )

        self.statut = StatutDemande.REFUSEE
        self.motif_rejet = motif
        self.date_validation = datetime.now()
        self._ajouter_log(f"Demande rejetée: {motif.valeur}")

    def _ajouter_log(self, message: str) -> None:
        """Ajoute une entrée au log de validation"""
        log_entry = LogValidation(
            timestamp=datetime.now(), message=message, statut=self.statut.value
        )
        self.log_validation.append(log_entry)

    def est_en_cours_validation(self) -> bool:
        """Vérifie si la validation est en cours"""
        return self.statut == StatutDemande.EN_COURS_VALIDATION

    def est_terminee(self) -> bool:
        """Vérifie si la demande est dans un état final"""
        return self.statut in [
            StatutDemande.APPROUVEE,
            StatutDemande.REFUSEE,
            StatutDemande.ECHEC_VALIDATION,
        ]


@dataclass
class EtapeValidation:
    """
    Entité représentant une étape du processus de validation.
    Utilisée pour l'orchestration du workflow complexe.
    """

    nom: str
    ordre: int
    executee: bool = False
    succes: bool = False
    message_erreur: Optional[str] = None
    timestamp_execution: Optional[datetime] = None

    def executer(self) -> None:
        """Marque l'étape comme en cours d'exécution"""
        self.executee = True
        self.timestamp_execution = datetime.now()

    def marquer_succes(self) -> None:
        """Marque l'étape comme réussie"""
        if not self.executee:
            raise EtapeValidationError(
                "L'étape doit être exécutée avant d'être marquée comme réussie"
            )
        self.succes = True

    def marquer_echec(self, erreur: str) -> None:
        """Marque l'étape comme échouée"""
        if not self.executee:
            raise EtapeValidationError(
                "L'étape doit être exécutée avant d'être marquée comme échouée"
            )
        self.succes = False
        self.message_erreur = erreur


@dataclass
class WorkflowValidation:
    """
    Entité orchestrant le workflow complet de validation.
    Gère les étapes et les rollbacks.
    """

    demande: DemandeReapprovisionnement
    etapes: List[EtapeValidation] = field(default_factory=list)
    etapes_reussies: List[EtapeValidation] = field(default_factory=list)

    def __post_init__(self):
        """Initialise les étapes du workflow"""
        if not self.etapes:
            self.etapes = [
                EtapeValidation("Diminuer stock central", 1),
                EtapeValidation("Augmenter stock local", 2),
                EtapeValidation("Mettre à jour statut", 3),
            ]

    def demarrer(self) -> None:
        """Démarre le workflow de validation"""
        self.demande.demarrer_validation()

    def executer_etape(self, numero_etape: int) -> EtapeValidation:
        """Exécute une étape spécifique"""
        if numero_etape < 1 or numero_etape > len(self.etapes):
            raise EtapeValidationError(f"Étape {numero_etape} invalide")

        etape = self.etapes[numero_etape - 1]
        etape.executer()
        return etape

    def marquer_etape_reussie(self, numero_etape: int) -> None:
        """Marque une étape comme réussie"""
        etape = self.etapes[numero_etape - 1]
        etape.marquer_succes()
        self.etapes_reussies.append(etape)

    def marquer_etape_echouee(self, numero_etape: int, erreur: str) -> None:
        """Marque une étape comme échouée et déclenche le rollback"""
        etape = self.etapes[numero_etape - 1]
        etape.marquer_echec(erreur)
        self.demande.marquer_echec_validation(f"Étape {numero_etape}: {erreur}")

    def finaliser_succes(self) -> None:
        """Finalise le workflow en cas de succès complet"""
        if len(self.etapes_reussies) == len(self.etapes):
            self.demande.marquer_approuvee()
        else:
            raise WorkflowError(
                "Toutes les étapes doivent être réussies pour finaliser"
            )

    def necessite_rollback(self) -> bool:
        """Vérifie si un rollback est nécessaire"""
        return len(self.etapes_reussies) > 0 and not all(e.succes for e in self.etapes)

    def get_etapes_a_rollback(self) -> List[EtapeValidation]:
        """Retourne les étapes qui nécessitent un rollback (ordre inverse)"""
        return list(reversed(self.etapes_reussies))
