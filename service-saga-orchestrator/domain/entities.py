from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid


class EtatSaga(Enum):
    """États de la machine d'état de la Saga simplifiée stock + commande"""
    EN_ATTENTE = "EN_ATTENTE"
    VERIFICATION_STOCK = "VERIFICATION_STOCK"
    STOCK_VERIFIE = "STOCK_VERIFIE"
    RESERVATION_STOCK = "RESERVATION_STOCK"
    STOCK_RESERVE = "STOCK_RESERVE"
    CREATION_COMMANDE = "CREATION_COMMANDE"
    COMMANDE_CREEE = "COMMANDE_CREEE"
    SAGA_TERMINEE = "SAGA_TERMINEE"
    # États d'échec et compensation
    ECHEC_STOCK_INSUFFISANT = "ECHEC_STOCK_INSUFFISANT"
    ECHEC_RESERVATION_STOCK = "ECHEC_RESERVATION_STOCK"
    ECHEC_CREATION_COMMANDE = "ECHEC_CREATION_COMMANDE"
    COMPENSATION_EN_COURS = "COMPENSATION_EN_COURS"
    SAGA_ANNULEE = "SAGA_ANNULEE"


class TypeEvenement(Enum):
    """Types d'événements dans la Saga simplifiée"""
    SAGA_DEMARRE = "SAGA_DEMARRE"
    STOCK_VERIFIE_SUCCES = "STOCK_VERIFIE_SUCCES"
    STOCK_VERIFIE_ECHEC = "STOCK_VERIFIE_ECHEC"
    STOCK_RESERVE_SUCCES = "STOCK_RESERVE_SUCCES"
    STOCK_RESERVE_ECHEC = "STOCK_RESERVE_ECHEC"
    COMMANDE_CREEE_SUCCES = "COMMANDE_CREEE_SUCCES"
    COMMANDE_CREEE_ECHEC = "COMMANDE_CREEE_ECHEC"
    COMPENSATION_DEMANDEE = "COMPENSATION_DEMANDEE"
    COMPENSATION_TERMINEE = "COMPENSATION_TERMINEE"
    SAGA_TERMINEE_SUCCES = "SAGA_TERMINEE_SUCCES"


@dataclass
class LigneCommande:
    """Value Object représentant une ligne de commande"""
    produit_id: str  # UUID du produit
    quantite: int
    prix_unitaire: float
    nom_produit: str = ""
    
    def __post_init__(self):
        if self.quantite <= 0:
            raise ValueError("La quantité doit être positive")
        if self.prix_unitaire < 0:
            raise ValueError("Le prix unitaire ne peut pas être négatif")
    
    @property
    def montant_ligne(self) -> float:
        return self.quantite * self.prix_unitaire


@dataclass
class EvenementSaga:
    """Value Object représentant un événement dans la Saga"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type_evenement: TypeEvenement = field(default=None)
    timestamp: datetime = field(default_factory=datetime.now)
    etat_precedent: EtatSaga = field(default=None)
    nouvel_etat: EtatSaga = field(default=None)
    donnees: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


@dataclass
class SagaCommande:
    """Entité racine d'agrégat représentant une Saga de commande simplifiée"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = field(default=None)  # UUID du client
    magasin_id: str = field(default="550e8400-e29b-41d4-a716-446655440000")  # UUID du magasin par défaut
    lignes_commande: List[LigneCommande] = field(default_factory=list)
    etat_actuel: EtatSaga = field(default=EtatSaga.EN_ATTENTE)
    evenements: List[EvenementSaga] = field(default_factory=list)
    date_creation: datetime = field(default_factory=datetime.now)
    date_derniere_modification: datetime = field(default_factory=datetime.now)
    
    # Données pour la coordination entre services
    reservation_stock_ids: Dict[str, str] = field(default_factory=dict)  # produit_id UUID -> reservation_id
    commande_finale_id: Optional[str] = None  # UUID de la commande finale
    donnees_contexte: Dict[str, Any] = field(default_factory=dict)  # Données contextuelles pour la saga
    
    # Métriques pour l'observabilité
    duree_etapes: Dict[str, float] = field(default_factory=dict)
    tentatives_par_etape: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation post-initialisation"""
        if self.lignes_commande and not all(ligne.quantite > 0 for ligne in self.lignes_commande):
            raise ValueError("Toutes les lignes doivent avoir une quantité positive")
    
    @property
    def montant_total(self) -> float:
        """Calcule le montant total de la commande"""
        return sum(ligne.montant_ligne for ligne in self.lignes_commande)
    
    @property
    def quantite_totale_articles(self) -> int:
        """Calcule la quantité totale d'articles dans la commande"""
        return sum(ligne.quantite for ligne in self.lignes_commande)
    
    @property
    def est_terminee(self) -> bool:
        """Vérifie si la saga est dans un état terminal"""
        etats_terminaux = {
            EtatSaga.SAGA_TERMINEE,
            EtatSaga.SAGA_ANNULEE
        }
        return self.etat_actuel in etats_terminaux
    
    @property
    def est_en_echec(self) -> bool:
        """Vérifie si la saga est en état d'échec"""
        etats_echec = {
            EtatSaga.ECHEC_STOCK_INSUFFISANT,
            EtatSaga.ECHEC_RESERVATION_STOCK,
            EtatSaga.ECHEC_CREATION_COMMANDE,
            EtatSaga.COMPENSATION_EN_COURS,
            EtatSaga.SAGA_ANNULEE
        }
        return self.etat_actuel in etats_echec
    
    @property
    def necessite_compensation(self) -> bool:
        """Vérifie si la saga nécessite une compensation (stock réservé à libérer)"""
        return (
            self.est_en_echec and 
            self.reservation_stock_ids and 
            self.etat_actuel not in {EtatSaga.ECHEC_STOCK_INSUFFISANT, EtatSaga.SAGA_ANNULEE}
        )
    
    def peut_transitionner_vers(self, nouvel_etat: EtatSaga) -> bool:
        """Vérifie si une transition d'état est valide"""
        transitions_valides = {
            EtatSaga.EN_ATTENTE: [EtatSaga.VERIFICATION_STOCK],
            EtatSaga.VERIFICATION_STOCK: [
                EtatSaga.STOCK_VERIFIE, 
                EtatSaga.ECHEC_STOCK_INSUFFISANT
            ],
            EtatSaga.STOCK_VERIFIE: [EtatSaga.RESERVATION_STOCK],
            EtatSaga.RESERVATION_STOCK: [
                EtatSaga.STOCK_RESERVE,
                EtatSaga.ECHEC_RESERVATION_STOCK
            ],
            EtatSaga.STOCK_RESERVE: [EtatSaga.CREATION_COMMANDE],
            EtatSaga.CREATION_COMMANDE: [
                EtatSaga.COMMANDE_CREEE,
                EtatSaga.ECHEC_CREATION_COMMANDE
            ],
            EtatSaga.COMMANDE_CREEE: [EtatSaga.SAGA_TERMINEE],
            # Transitions de compensation
            EtatSaga.ECHEC_STOCK_INSUFFISANT: [EtatSaga.SAGA_ANNULEE],
            EtatSaga.ECHEC_RESERVATION_STOCK: [EtatSaga.SAGA_ANNULEE],
            EtatSaga.ECHEC_CREATION_COMMANDE: [EtatSaga.COMPENSATION_EN_COURS],
            EtatSaga.COMPENSATION_EN_COURS: [EtatSaga.SAGA_ANNULEE],
        }
        
        return nouvel_etat in transitions_valides.get(self.etat_actuel, [])
    
    def transitionner_vers(self, nouvel_etat: EtatSaga, evenement_type: TypeEvenement, 
                          donnees: Dict[str, Any] = None, message: str = None):
        """Effectue une transition d'état avec enregistrement d'événement"""
        if not self.peut_transitionner_vers(nouvel_etat):
            raise ValueError(
                f"Transition invalide de {self.etat_actuel} vers {nouvel_etat}"
            )
        
        # Créer l'événement de transition
        evenement = EvenementSaga(
            type_evenement=evenement_type,
            etat_precedent=self.etat_actuel,
            nouvel_etat=nouvel_etat,
            donnees=donnees or {},
            message=message
        )
        
        # Effectuer la transition
        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat
        self.date_derniere_modification = datetime.now()
        
        # Enregistrer l'événement
        self.evenements.append(evenement)
        
        # Mettre à jour les métriques
        self._mettre_a_jour_metriques(ancien_etat, nouvel_etat)
    
    def _mettre_a_jour_metriques(self, ancien_etat: EtatSaga, nouvel_etat: EtatSaga):
        """Met à jour les métriques de performance"""
        # Calculer la durée de l'étape précédente
        if len(self.evenements) >= 2:
            duree = (self.evenements[-1].timestamp - self.evenements[-2].timestamp).total_seconds()
            self.duree_etapes[ancien_etat.value] = duree
        
        # Incrémenter le nombre de tentatives
        etape_key = nouvel_etat.value
        self.tentatives_par_etape[etape_key] = self.tentatives_par_etape.get(etape_key, 0) + 1
    
    def ajouter_ligne_commande(self, ligne: LigneCommande):
        """Ajoute une ligne à la commande (seulement si en attente)"""
        if self.etat_actuel != EtatSaga.EN_ATTENTE:
            raise ValueError("Impossible de modifier une commande en cours de traitement")
        
        self.lignes_commande.append(ligne)
        self.date_derniere_modification = datetime.now()
    
    def ajouter_reservation_stock(self, produit_id: int, reservation_id: str):
        """Enregistre un ID de réservation de stock pour un produit"""
        self.reservation_stock_ids[produit_id] = reservation_id
    
    def obtenir_resume_execution(self) -> Dict[str, Any]:
        """Retourne un résumé de l'exécution de la saga"""
        duree_totale = 0
        if self.evenements:
            duree_totale = (self.evenements[-1].timestamp - self.evenements[0].timestamp).total_seconds()
        
        return {
            "saga_id": self.id,
            "client_id": self.client_id,
            "magasin_id": self.magasin_id,
            "etat_actuel": self.etat_actuel.value,
            "est_terminee": self.est_terminee,
            "est_en_echec": self.est_en_echec,
            "necessite_compensation": self.necessite_compensation,
            "montant_total": self.montant_total,
            "quantite_totale_articles": self.quantite_totale_articles,
            "nombre_lignes": len(self.lignes_commande),
            "nombre_evenements": len(self.evenements),
            "duree_totale_secondes": duree_totale,
            "duree_par_etape": self.duree_etapes,
            "tentatives_par_etape": self.tentatives_par_etape,
            "reservations_actives": len(self.reservation_stock_ids),
            "commande_finale_id": self.commande_finale_id,
            "date_creation": self.date_creation.isoformat(),
            "date_derniere_modification": self.date_derniere_modification.isoformat()
        }
    
    def obtenir_lignes_pour_verification_stock(self) -> List[Dict[str, Any]]:
        """Retourne les lignes formatées pour l'appel au service inventaire"""
        return [
            {
                "produit_id": ligne.produit_id,
                "quantite_demandee": ligne.quantite,
                "nom_produit": ligne.nom_produit
            }
            for ligne in self.lignes_commande
        ]
    
    def obtenir_donnees_pour_commande(self) -> Dict[str, Any]:
        """Retourne les données formatées pour créer la commande finale"""
        return {
            "client_id": self.client_id,
            "magasin_id": self.magasin_id,
            "montant_total": self.montant_total,
            "lignes": [
                {
                    "produit_id": ligne.produit_id,
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "montant_ligne": ligne.montant_ligne
                }
                for ligne in self.lignes_commande
            ],
            "saga_id": self.id  # Pour traçabilité
        } 