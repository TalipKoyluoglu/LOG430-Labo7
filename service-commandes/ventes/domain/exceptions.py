"""
Exceptions du domaine Ventes
Exceptions métier spécifiques au domaine
"""


class DomainError(Exception):
    """Base class pour toutes les erreurs du domaine"""

    pass


class VenteError(DomainError):
    """Erreurs liées aux ventes"""

    pass


class VenteDejaAnnuleeError(VenteError):
    """Erreur quand on essaie d'annuler une vente déjà annulée"""

    pass


class StockInsuffisantError(VenteError):
    """Erreur quand le stock est insuffisant pour une vente"""

    def __init__(
        self, produit_id: str, quantite_demandee: int, quantite_disponible: int
    ):
        self.produit_id = produit_id
        self.quantite_demandee = quantite_demandee
        self.quantite_disponible = quantite_disponible
        super().__init__(
            f"Stock insuffisant pour le produit {produit_id}. "
            f"Demandé: {quantite_demandee}, Disponible: {quantite_disponible}"
        )


class MagasinInexistantError(VenteError):
    """Erreur quand le magasin n'existe pas"""

    pass


class ProduitInexistantError(VenteError):
    """Erreur quand le produit n'existe pas"""

    pass


class VenteInvalideError(VenteError):
    """Erreur quand une vente est invalide"""

    pass
