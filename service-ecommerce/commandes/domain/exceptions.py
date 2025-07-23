"""
Exceptions métier du domaine Check-out
"""

from typing import List, Dict, Any


class CheckoutDomainError(Exception):
    """Exception de base pour le domaine Check-out"""

    pass


class CheckoutInvalideError(CheckoutDomainError):
    """Exception levée quand le processus de check-out est invalide"""

    pass


class PanierVideError(CheckoutDomainError):
    """Exception levée quand on tente un check-out avec un panier vide"""

    pass


class StockInsuffisantError(CheckoutDomainError):
    """Exception levée quand le stock est insuffisant pour un ou plusieurs produits"""

    def __init__(self, message: str, stocks_insuffisants: List[Dict[str, Any]]):
        super().__init__(message)
        self.stocks_insuffisants = stocks_insuffisants


class ClientInvalideError(CheckoutDomainError):
    """Exception levée quand le client n'est pas valide pour une commande"""

    pass


class AdresseLivraisonInvalideError(CheckoutDomainError):
    """Exception levée pour une adresse de livraison invalide"""

    pass


class CheckoutError(CheckoutDomainError):
    """Exception générale pour les erreurs de check-out"""

    pass


class AdresseInvalideError(CheckoutDomainError):
    """Exception pour adresse invalide (alias pour compatibilité)"""

    pass


class ServiceExterneIndisponibleError(CheckoutDomainError):
    """Exception levée quand un service externe est indisponible"""

    def __init__(self, service_name: str, message: str):
        super().__init__(f"Service {service_name} indisponible: {message}")
        self.service_name = service_name


class CreationCommandeEchecError(CheckoutDomainError):
    """Exception levée quand la création de commande externe échoue"""

    pass
