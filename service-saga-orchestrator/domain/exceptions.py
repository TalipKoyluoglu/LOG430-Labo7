"""
Exceptions métier du domaine Saga simplifiée
"""


class SagaException(Exception):
    """Exception de base pour le domaine Saga"""
    pass


class EtatTransitionInvalideException(SagaException):
    """Exception levée lors d'une transition d'état invalide"""
    def __init__(self, etat_actuel, nouvel_etat):
        self.etat_actuel = etat_actuel
        self.nouvel_etat = nouvel_etat
        super().__init__(f"Transition invalide de {etat_actuel} vers {nouvel_etat}")


class SagaIntrouvableException(SagaException):
    """Exception levée quand une saga n'est pas trouvée"""
    def __init__(self, saga_id):
        self.saga_id = saga_id
        super().__init__(f"Saga {saga_id} introuvable")


class SagaDejaTermineeException(SagaException):
    """Exception levée quand on tente de modifier une saga terminée"""
    def __init__(self, saga_id, etat_actuel):
        self.saga_id = saga_id
        self.etat_actuel = etat_actuel
        super().__init__(f"Saga {saga_id} déjà terminée dans l'état {etat_actuel}")


class ServiceExterneIndisponibleException(SagaException):
    """Exception levée quand un service externe est indisponible"""
    def __init__(self, service_name, action):
        self.service_name = service_name
        self.action = action
        super().__init__(f"Service {service_name} indisponible pour l'action: {action}")


class StockInsuffisantException(SagaException):
    """Exception levée quand le stock est insuffisant"""
    def __init__(self, produit_id, quantite_demandee, quantite_disponible):
        self.produit_id = produit_id
        self.quantite_demandee = quantite_demandee
        self.quantite_disponible = quantite_disponible
        super().__init__(
            f"Stock insuffisant pour produit {produit_id}: "
            f"demandé {quantite_demandee}, disponible {quantite_disponible}"
        )


class ReservationStockEchecException(SagaException):
    """Exception levée quand la réservation de stock échoue"""
    def __init__(self, produit_id, raison="Réservation impossible"):
        self.produit_id = produit_id
        self.raison = raison
        super().__init__(f"Échec réservation stock produit {produit_id}: {raison}")


class CreationCommandeEchecException(SagaException):
    """Exception levée quand la création de commande échoue"""
    def __init__(self, raison="Erreur lors de la création"):
        self.raison = raison
        super().__init__(f"Échec création commande: {raison}")


class CompensationEchecException(SagaException):
    """Exception levée quand une action de compensation échoue"""
    def __init__(self, action_compensation, raison):
        self.action_compensation = action_compensation
        self.raison = raison
        super().__init__(f"Échec de compensation {action_compensation}: {raison}")


class DonneesInvalidesException(SagaException):
    """Exception levée pour des données invalides dans la saga"""
    def __init__(self, message):
        super().__init__(f"Données invalides: {message}") 