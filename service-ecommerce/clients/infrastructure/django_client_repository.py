"""
Implémentation Django du Repository Client - Infrastructure
"""

import uuid
import logging
from typing import List, Optional

from ..application.repositories.client_repository import ClientRepository
from ..domain.entities import Client
from ..domain.value_objects import Email, NomComplet, Adresse
from ..models import ClientModel

logger = logging.getLogger("clients")


class DjangoClientRepository(ClientRepository):
    """
    Implémentation Django du Repository Client
    Convertit entre les entités du domaine et les modèles Django
    """

    def save(self, client: Client) -> None:
        """
        Sauvegarde un client (création ou mise à jour)
        """
        try:
            # Convertir l'entité domaine vers le modèle Django
            django_model, created = ClientModel.objects.update_or_create(
                id=client.id,
                defaults={
                    "prenom": client.nom_complet.prenom,
                    "nom": client.nom_complet.nom,
                    "email": str(client.email),
                    "telephone": client.telephone,
                    "adresse_rue": client.adresse.rue,
                    "adresse_ville": client.adresse.ville,
                    "adresse_code_postal": client.adresse.code_postal,
                    "adresse_province": client.adresse.province,
                    "adresse_pays": client.adresse.pays,
                    "actif": client.actif,
                },
            )

            action = "créé" if created else "mis à jour"
            logger.debug(f"Client {action}: {client.id}")

        except Exception as e:
            logger.error(
                f"Erreur lors de la sauvegarde du client {client.id}: {str(e)}"
            )
            raise

    def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        """
        Récupère un client par son ID
        """
        try:
            django_model = ClientModel.objects.get(id=client_id)
            return self._to_domain_entity(django_model)
        except ClientModel.DoesNotExist:
            logger.debug(f"Client non trouvé: {client_id}")
            return None
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération du client {client_id}: {str(e)}"
            )
            raise

    def get_by_email(self, email: Email) -> Optional[Client]:
        """
        Récupère un client par son email
        """
        try:
            django_model = ClientModel.objects.get(email=str(email))
            return self._to_domain_entity(django_model)
        except ClientModel.DoesNotExist:
            logger.debug(f"Client non trouvé pour email: {email}")
            return None
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération du client par email {email}: {str(e)}"
            )
            raise

    def exists_by_email(self, email: Email) -> bool:
        """
        Vérifie si un client existe avec cet email
        """
        try:
            return ClientModel.objects.filter(email=str(email)).exists()
        except Exception as e:
            logger.error(
                f"Erreur lors de la vérification d'existence de l'email {email}: {str(e)}"
            )
            raise

    def get_all_active(self) -> List[Client]:
        """
        Récupère tous les clients actifs
        """
        try:
            django_models = ClientModel.objects.filter(actif=True)
            return [self._to_domain_entity(model) for model in django_models]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des clients actifs: {str(e)}")
            raise

    def delete(self, client_id: uuid.UUID) -> bool:
        """
        Supprime un client (soft delete)
        """
        try:
            updated = ClientModel.objects.filter(id=client_id).update(actif=False)
            success = updated > 0
            if success:
                logger.debug(f"Client désactivé: {client_id}")
            return success
        except Exception as e:
            logger.error(
                f"Erreur lors de la suppression du client {client_id}: {str(e)}"
            )
            raise

    def _to_domain_entity(self, django_model: ClientModel) -> Client:
        """
        Convertit un modèle Django vers une entité du domaine
        """
        try:
            # Créer les value objects
            nom_complet = NomComplet(prenom=django_model.prenom, nom=django_model.nom)

            email = Email(django_model.email)

            adresse = Adresse(
                rue=django_model.adresse_rue,
                ville=django_model.adresse_ville,
                code_postal=django_model.adresse_code_postal,
                province=django_model.adresse_province,
                pays=django_model.adresse_pays,
            )

            # Créer l'entité domaine
            client = Client(
                id=django_model.id,
                nom_complet=nom_complet,
                email=email,
                adresse=adresse,
                telephone=django_model.telephone,
                date_creation=django_model.date_creation,
            )

            # Restaurer l'état actif/inactif
            if not django_model.actif:
                client._actif = False

            # Restaurer la date de modification
            client._date_modification = django_model.date_modification

            return client

        except Exception as e:
            logger.error(f"Erreur lors de la conversion vers entité domaine: {str(e)}")
            raise
