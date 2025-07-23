"""
Use Case: Lister tous les Clients actifs
Fonctionnalité métier pour récupérer la liste des clients e-commerce
"""

import logging
from typing import List, Dict, Any

from ..repositories.client_repository import ClientRepository

logger = logging.getLogger("clients")


class ListerClientsUseCase:
    """
    Use Case: Lister tous les clients actifs

    Utilisé pour afficher la liste des comptes clients
    dans l'interface d'administration e-commerce
    """

    def __init__(self, client_repository: ClientRepository):
        self._client_repo = client_repository

    def execute(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste de tous les clients actifs

        Returns:
            List[Dict] contenant les informations de chaque client
        """

        logger.debug("Récupération de la liste des clients actifs")

        # Récupérer tous les clients actifs
        clients = self._client_repo.get_all_active()

        # Convertir en format de réponse
        clients_data = []
        for client in clients:
            client_info = {
                "id": str(client.id),
                "nom_complet": client.nom_complet.affichage(),
                "email": str(client.email),
                "telephone": client.telephone,
                "adresse": {
                    "rue": client.adresse.rue,
                    "ville": client.adresse.ville,
                    "code_postal": client.adresse.code_postal,
                    "province": client.adresse.province,
                    "pays": client.adresse.pays,
                    "adresse_complete": client.adresse.adresse_complete(),
                },
                "date_creation": (
                    client.date_creation.isoformat() if client.date_creation else None
                ),
                "date_modification": (
                    client.date_modification.isoformat()
                    if client.date_modification
                    else None
                ),
                "actif": client.actif,
            }
            clients_data.append(client_info)

        logger.debug(f"Liste de {len(clients_data)} clients récupérée")

        return clients_data
