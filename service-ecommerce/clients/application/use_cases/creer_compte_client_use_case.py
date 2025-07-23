"""
Use Case: Créer un Compte Client
Fonctionnalité métier complète pour créer un nouveau client
"""

import uuid
import logging
from typing import Dict, Any

from ..repositories.client_repository import ClientRepository
from ...domain.entities import Client
from ...domain.value_objects import CommandeCreationClient, Email, NomComplet, Adresse
from ...domain.exceptions import EmailDejaUtiliseError, DonneesClientInvalidesError

logger = logging.getLogger("clients")


class CreerCompteClientUseCase:
    """
    Use Case: Créer un nouveau compte client

    Orchestration complète de la fonctionnalité métier:
    1. Validation des données métier
    2. Vérification unicité email
    3. Création de l'entité Client riche
    4. Persistance via Repository
    """

    def __init__(self, client_repository: ClientRepository):
        self._client_repo = client_repository

    def execute(self, commande: CommandeCreationClient) -> Dict[str, Any]:
        """
        Exécute le cas d'usage de création de compte client

        Args:
            commande: CommandeCreationClient contenant les données du nouveau client

        Returns:
            Dict contenant les détails du client créé

        Raises:
            EmailDejaUtiliseError: Si l'email est déjà utilisé
            DonneesClientInvalidesError: Si les données sont invalides
        """

        logger.info(f"Début création compte client pour email: {commande.email}")

        try:
            # 1. Validation métier de l'unicité de l'email
            if self._client_repo.exists_by_email(commande.email):
                logger.warning(
                    f"Tentative de création avec email existant: {commande.email}"
                )
                raise EmailDejaUtiliseError(str(commande.email))

            # 2. Création de l'entité Client riche (avec logique métier)
            client_id = uuid.uuid4()
            client = Client(
                id=client_id,
                nom_complet=commande.nom_complet,
                email=commande.email,
                adresse=commande.adresse,
                telephone=commande.telephone,
            )

            # 3. Persistance via Repository
            self._client_repo.save(client)

            logger.info(
                f"Compte client créé avec succès: {client_id} - {commande.email}"
            )

            # 4. Retour des données pour la réponse API
            return {
                "success": True,
                "client": {
                    "id": str(client.id),
                    "nom_complet": client.nom_complet.affichage(),
                    "email": str(client.email),
                    "adresse_complete": client.adresse.adresse_complete(),
                    "telephone": client.telephone,
                    "date_creation": client.date_creation.isoformat(),
                    "actif": client.actif,
                },
            }

        except (EmailDejaUtiliseError, DonneesClientInvalidesError):
            # Re-lancer les exceptions métier
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création du compte client: {str(e)}")
            raise DonneesClientInvalidesError("general", "création compte", str(e))
