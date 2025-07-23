"""
Implémentation Django du MagasinRepository
Infrastructure layer - convertit entre entités domain et modèles Django
"""

from typing import List, Optional
from uuid import UUID

from ..application.repositories.magasin_repository import MagasinRepository
from ..domain.entities import Magasin
from ..models import Magasin as MagasinDjango


class DjangoMagasinRepository(MagasinRepository):
    """
    Implémentation concrète du MagasinRepository utilisant Django ORM
    Responsabilité: Conversion entités domain <-> modèles Django
    """

    def get_by_id(self, magasin_id: UUID) -> Optional[Magasin]:
        """Récupère un magasin par son ID et le convertit en entité domain"""
        try:
            magasin_django = MagasinDjango.objects.get(id=magasin_id)
            return self._to_domain_entity(magasin_django)
        except MagasinDjango.DoesNotExist:
            return None

    def get_all(self) -> List[Magasin]:
        """Récupère tous les magasins et les convertit en entités domain"""
        magasins_django = MagasinDjango.objects.all()
        return [self._to_domain_entity(magasin) for magasin in magasins_django]

    def save(self, magasin: Magasin) -> None:
        """Persiste un magasin en base via Django ORM"""
        try:
            magasin_django, created = MagasinDjango.objects.get_or_create(
                id=magasin.id, defaults={"nom": magasin.nom, "adresse": magasin.adresse}
            )

            # Mise à jour si existant
            if not created:
                magasin_django.nom = magasin.nom
                magasin_django.adresse = magasin.adresse
                magasin_django.save()

        except Exception as e:
            raise RuntimeError(f"Erreur lors de la persistance du magasin: {e}")

    def _to_domain_entity(self, magasin_django: MagasinDjango) -> Magasin:
        """Convertit un modèle Django en entité domain"""
        return Magasin(
            id=UUID(str(magasin_django.id)),
            nom=str(magasin_django.nom),
            adresse=str(magasin_django.adresse),
        )
