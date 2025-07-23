"""
Use Case : Lister les demandes de réapprovisionnement en attente
Récupération avec enrichissement métier.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import logging

from ...domain.value_objects import Quantite
from ...domain.exceptions import CommunicationServiceError
from ..repositories.demande_repository import DemandeRepository

logger = logging.getLogger(__name__)


@dataclass
class ListerDemandesQuery:
    """Query pour lister les demandes (pattern CQRS)"""

    pass


@dataclass
class ListerDemandesResult:
    """Résultat de la liste des demandes avec enrichissement métier"""

    demandes: List[Dict[str, Any]]
    count: int
    statistiques: Dict[str, Any]


class ListerDemandesUseCase:
    """
    Use Case métier : Lister les demandes en attente avec enrichissement

    Responsabilités :
    1. Récupérer les demandes depuis le repository
    2. Enrichir avec des informations métier (Value Objects)
    3. Calculer des statistiques métier
    4. Formater pour l'affichage
    """

    def __init__(self, demande_repository: DemandeRepository):
        self.demande_repository = demande_repository

    def execute(self, query: ListerDemandesQuery) -> ListerDemandesResult:
        """
        Exécute la récupération et l'enrichissement des demandes

        Workflow DDD :
        1. Récupérer les données brutes (Repository)
        2. Enrichir avec des règles métier (Value Objects)
        3. Calculer des statistiques métier
        4. Formater le résultat
        """
        logger.info("Début Use Case: Lister demandes en attente")

        try:
            # 1. Récupérer les demandes brutes
            demandes_brutes = self.demande_repository.get_demandes_en_attente()

            # 2. Enrichir avec logique métier
            demandes_enrichies = []
            quantites_importantes = 0
            quantites_critiques = 0
            quantite_totale = 0

            for demande_data in demandes_brutes:
                # Enrichissement avec Value Objects
                quantite = Quantite.from_int(demande_data.get("quantite", 0))

                demande_enrichie = {
                    **demande_data,
                    # Enrichissements métier via Value Objects
                    "est_quantite_importante": quantite.est_importante(),
                    "est_quantite_critique": quantite.est_critique(),
                    "quantite_formatee": str(quantite),
                }

                demandes_enrichies.append(demande_enrichie)

                # Calculs statistiques métier
                if quantite.est_importante():
                    quantites_importantes += 1
                if quantite.est_critique():
                    quantites_critiques += 1
                quantite_totale += int(quantite)

            # 3. Calculer statistiques métier
            statistiques = {
                "total_demandes": len(demandes_enrichies),
                "demandes_importantes": quantites_importantes,
                "demandes_critiques": quantites_critiques,
                "quantite_totale_demandee": quantite_totale,
                "pourcentage_important": round(
                    (
                        (quantites_importantes / len(demandes_enrichies) * 100)
                        if demandes_enrichies
                        else 0
                    ),
                    2,
                ),
            }

            logger.info(
                f"Use Case réussi: {len(demandes_enrichies)} demandes récupérées"
            )

            return ListerDemandesResult(
                demandes=demandes_enrichies,
                count=len(demandes_enrichies),
                statistiques=statistiques,
            )

        except CommunicationServiceError as e:
            logger.error(f"Erreur communication: {e}")
            # Retourner un résultat vide plutôt qu'une exception
            return ListerDemandesResult(
                demandes=[], count=0, statistiques={"error": str(e)}
            )

        except Exception as e:
            logger.error(f"Erreur critique Use Case: {e}")
            return ListerDemandesResult(
                demandes=[],
                count=0,
                statistiques={"error": "Erreur interne lors de la récupération"},
            )
