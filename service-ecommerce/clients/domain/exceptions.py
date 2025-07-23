"""
Exceptions métier du domaine Clients
"""


class ClientDomainError(Exception):
    """Exception de base pour le domaine Client"""

    pass


class ClientInactifError(ClientDomainError):
    """Exception levée quand un client inactif tente une action interdite"""

    def __init__(self, message: str = "Client inactif"):
        self.message = message
        super().__init__(self.message)


class EmailDejaUtiliseError(ClientDomainError):
    """Exception levée quand un email est déjà utilisé par un autre client"""

    def __init__(self, email: str):
        self.email = email
        self.message = f"L'email {email} est déjà utilisé par un autre client"
        super().__init__(self.message)


class ClientInexistantError(ClientDomainError):
    """Exception levée quand un client demandé n'existe pas"""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.message = f"Client {client_id} non trouvé"
        super().__init__(self.message)


class DonneesClientInvalidesError(ClientDomainError):
    """Exception levée pour des données client invalides"""

    def __init__(self, champ: str, valeur: str, raison: str):
        self.champ = champ
        self.valeur = valeur
        self.raison = raison
        self.message = f"Données invalides pour {champ}: {raison}"
        super().__init__(self.message)
