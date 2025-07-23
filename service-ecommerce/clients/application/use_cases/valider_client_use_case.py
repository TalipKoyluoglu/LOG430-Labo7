"""
Use Case: Valider un Client pour Commande
Fonctionnalité métier pour valider qu'un client peut passer commande
"""

import uuid
import logging
from typing import Dict, Any

from ..repositories.client_repository import ClientRepository
from ...domain.exceptions import ClientInexistantError, ClientInactifError

logger = logging.getLogger("clients")


class ValiderClientUseCase:
    """
    Use Case: Valider un client pour une commande

    Utilisé par le service-commandes pour vérifier qu'un client
    existe et peut passer une commande
    """

    def __init__(self, client_repository: ClientRepository):
        self._client_repo = client_repository

    def execute(self, client_id: uuid.UUID) -> Dict[str, Any]:
        """
        Valide qu'un client peut passer une commande

        Args:
            client_id: UUID du client à valider

        Returns:
            Dict contenant les informations de validation du client

        Raises:
            ClientInexistantError: Si le client n'existe pas
            ClientInactifError: Si le client est inactif
        """

        logger.debug(f"Validation client pour commande: {client_id}")

        # Récupérer le client
        client = self._client_repo.get_by_id(client_id)

        if not client:
            logger.warning(f"Client non trouvé: {client_id}")
            raise ClientInexistantError(str(client_id))

        # Utiliser la logique métier de l'entité
        try:
            validation_info = client.valider_pour_commande()

            logger.debug(f"Client validé pour commande: {client_id}")

            return {"valid": True, **validation_info}

        except ClientInactifError as e:
            logger.warning(f"Client inactif tentant de passer commande: {client_id}")
            raise e
