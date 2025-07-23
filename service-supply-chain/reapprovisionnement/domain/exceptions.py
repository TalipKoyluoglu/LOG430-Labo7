"""
Exceptions métier du domaine Réapprovisionnement
Exceptions spécifiques aux règles et contraintes métier.
"""


class ReapprovisionnementDomainError(Exception):
    """Exception de base pour tous les erreurs du domaine réapprovisionnement"""

    pass


class DemandeInvalideError(ReapprovisionnementDomainError):
    """Erreur lorsqu'une demande est dans un état invalide"""

    def __init__(self, message: str, demande_id: str = None):
        self.demande_id = demande_id
        super().__init__(message)


class WorkflowError(ReapprovisionnementDomainError):
    """Erreur dans le workflow de validation"""

    def __init__(self, message: str, etape: str = None):
        self.etape = etape
        super().__init__(message)


class EtapeValidationError(ReapprovisionnementDomainError):
    """Erreur lors de l'exécution d'une étape de validation"""

    def __init__(self, message: str, numero_etape: int = None):
        self.numero_etape = numero_etape
        super().__init__(message)


class RollbackError(ReapprovisionnementDomainError):
    """Erreur lors du rollback d'une opération"""

    def __init__(self, message: str, etapes_echouees: list = None):
        self.etapes_echouees = etapes_echouees or []
        super().__init__(message)


class ValidationMetierError(ReapprovisionnementDomainError):
    """Erreur de validation des règles métier"""

    def __init__(self, message: str, champ: str = None, valeur=None):
        self.champ = champ
        self.valeur = valeur
        super().__init__(message)


class CommunicationServiceError(ReapprovisionnementDomainError):
    """Erreur de communication avec un service externe"""

    def __init__(self, message: str, service: str = None, status_code: int = None):
        self.service = service
        self.status_code = status_code
        super().__init__(message)


class StatutInvalideError(DemandeInvalideError):
    """Erreur lorsqu'une transition de statut est invalide"""

    def __init__(self, statut_actuel: str, statut_demande: str, demande_id: str = None):
        message = (
            f"Impossible de passer du statut '{statut_actuel}' à '{statut_demande}'"
        )
        self.statut_actuel = statut_actuel
        self.statut_demande = statut_demande
        super().__init__(message, demande_id)


class QuantiteInvalideError(ValidationMetierError):
    """Erreur lorsqu'une quantité est invalide"""

    def __init__(self, quantite: int, raison: str = ""):
        message = f"Quantité invalide: {quantite}"
        if raison:
            message += f" - {raison}"
        super().__init__(message, "quantite", quantite)


class StockInsuffisantError(ReapprovisionnementDomainError):
    """Erreur lorsque le stock est insuffisant pour une opération"""

    def __init__(
        self, produit_id: str, quantite_demandee: int, quantite_disponible: int
    ):
        message = f"Stock insuffisant pour le produit {produit_id}: {quantite_disponible} disponible, {quantite_demandee} demandé"
        self.produit_id = produit_id
        self.quantite_demandee = quantite_demandee
        self.quantite_disponible = quantite_disponible
        super().__init__(message)
