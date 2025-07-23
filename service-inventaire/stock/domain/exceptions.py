"""
Exceptions métier du domaine Inventaire
Exceptions spécifiques aux règles métier de gestion de stock.
"""


class InventaireDomainError(Exception):
    """Exception de base pour toutes les erreurs du domaine Inventaire"""

    pass


class StockInsuffisantError(InventaireDomainError):
    """
    Exception levée lorsque le stock est insuffisant pour une opération.
    Utilisée dans les règles métier de diminution de stock.
    """

    pass


class StockNegatifError(InventaireDomainError):
    """
    Exception levée lorsqu'une opération tenterait de créer un stock négatif.
    Protège l'intégrité métier des quantités.
    """

    pass


class QuantiteInvalideError(InventaireDomainError):
    """
    Exception levée pour les quantités invalides (négatives, trop grandes, etc.).
    Validation des Value Objects de quantité.
    """

    pass


class DemandeStatutInvalideError(InventaireDomainError):
    """
    Exception levée lors de transitions de statut invalides pour les demandes.
    Protège les règles de workflow métier.
    """

    pass


class ProduitInexistantError(InventaireDomainError):
    """
    Exception levée lorsqu'un produit référencé n'existe pas.
    Validation de l'intégrité référentielle métier.
    """

    pass


class MagasinInexistantError(InventaireDomainError):
    """
    Exception levée lorsqu'un magasin référencé n'existe pas.
    Validation de l'intégrité référentielle métier.
    """

    pass


class TransfertImpossibleError(InventaireDomainError):
    """
    Exception levée lorsqu'un transfert de stock ne peut pas être effectué.
    Validation des règles de transfert entre stocks.
    """

    pass


class SeuilStockInvalideError(InventaireDomainError):
    """
    Exception levée pour des seuils de stock incohérents.
    Validation des règles de configuration des seuils.
    """

    pass


class MouvementStockInvalideError(InventaireDomainError):
    """
    Exception levée pour des mouvements de stock invalides.
    Validation des opérations de stock.
    """

    pass
