"""
Exceptions métier du domaine Panier
"""


class PanierDomainError(Exception):
    """Exception de base pour le domaine Panier"""

    pass


class PanierVideError(PanierDomainError):
    """Exception levée quand on tente une opération sur un panier vide"""

    pass


class ProduitNonTrouveError(PanierDomainError):
    """Exception levée quand un produit n'est pas trouvé dans le panier"""

    pass


class QuantiteInvalideError(PanierDomainError):
    """Exception levée pour une quantité invalide"""

    pass


class StockInsuffisantError(PanierDomainError):
    """Exception levée quand le stock est insuffisant"""

    pass


class ProduitInexistantError(PanierDomainError):
    """Exception levée quand un produit n'existe pas dans le catalogue"""

    pass
