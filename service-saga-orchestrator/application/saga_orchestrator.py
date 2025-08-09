"""
Orchestrateur de Saga synchrone pour la coordination stock + commande
"""

import requests
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from domain.entities import SagaCommande, EtatSaga, TypeEvenement, LigneCommande
from domain.exceptions import (
    ServiceExterneIndisponibleException,
    StockInsuffisantException,
    ReservationStockEchecException,
    CreationCommandeEchecException,
    CompensationEchecException,
)
from infrastructure.prometheus_metrics import metrics_collector

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    """
    Orchestrateur synchrone pour les sagas de commande
    Coordonne les appels via Kong API Gateway vers les 3 microservices :
    - service-catalogue : informations produit
    - service-inventaire : gestion stock
    - service-commandes : création vente finale
    """

    def __init__(
        self,
        kong_gateway_url: str = None,
        timeout: int = None
    ):
        # Configuration depuis Django settings si disponible
        try:
            from django.conf import settings
            config = settings.SAGA_ORCHESTRATOR_CONFIG
            
            self.kong_gateway_url = kong_gateway_url or config['KONG_GATEWAY']['BASE_URL']
            self.timeout = timeout or config['TIMEOUTS']['DEFAULT_TIMEOUT']
            api_key = config['KONG_GATEWAY']['API_KEY']
            
            # URLs des services via Kong depuis la configuration
            self.service_catalogue_url = config['SERVICES']['CATALOGUE_URL']
            self.service_inventaire_url = config['SERVICES']['INVENTAIRE_URL'] 
            self.service_commandes_url = config['SERVICES']['COMMANDES_URL']
            
        except (ImportError, KeyError):
            # Fallback si Django n'est pas disponible
            self.kong_gateway_url = kong_gateway_url or "http://kong:8080"
            self.timeout = timeout or 30
            api_key = 'magasin-secret-key-2025'
            
            # URLs des services via Kong (fallback)
            self.service_catalogue_url = f"{self.kong_gateway_url}/api/catalogue"
            self.service_inventaire_url = f"{self.kong_gateway_url}/api/inventaire" 
            self.service_commandes_url = f"{self.kong_gateway_url}/api/commandes"
        
        # Headers obligatoires pour Kong API Gateway
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
        
        logger.info(f"SagaOrchestrator initialisé avec Kong Gateway:")
        logger.info(f"  - Kong Gateway: {self.kong_gateway_url}")
        logger.info(f"  - Service Catalogue: {self.service_catalogue_url}")
        logger.info(f"  - Service Inventaire: {self.service_inventaire_url}")
        logger.info(f"  - Service Commandes: {self.service_commandes_url}")
        logger.info(f"  - API Key: {self.headers['X-API-Key']}")

    def executer_saga(self, saga: SagaCommande, saga_repository=None) -> Dict[str, Any]:
        """
        Exécute une saga de commande de manière synchrone avec persistance
        
        Args:
            saga: La saga à exécuter
            saga_repository: Repository pour la persistance (optionnel)
            
        Returns:
            Résumé de l'exécution
            
        Raises:
            Various SagaException selon l'étape qui échoue
        """
        try:
            start_time = time.time()
            logger.info(f"Démarrage de la saga {saga.id}")
            
            # Métriques : saga démarrée
            metrics_collector.record_saga_started(saga)
            
            # Démarrer la saga
            saga.transitionner_vers(
                EtatSaga.VERIFICATION_STOCK,
                TypeEvenement.SAGA_DEMARRE,
                message="Saga démarrée, vérification du stock"
            )
            
            # Persister après démarrage
            if saga_repository:
                saga_repository.save(saga)
            
            # Étape 1: Vérification du stock
            self._verifier_stock(saga)
            metrics_collector.record_saga_step(saga, "VERIFICATION_STOCK", "SUCCESS")
            if saga_repository:
                saga_repository.save(saga)
            
            # Étape 2: Récupération informations produit  
            self._recuperer_informations_produit(saga)
            metrics_collector.record_saga_step(saga, "RECUPERATION_PRODUIT", "SUCCESS")
            if saga_repository:
                saga_repository.save(saga)
            
            # Étape 3: Réservation du stock
            self._reserver_stock(saga)
            metrics_collector.record_saga_step(saga, "RESERVATION_STOCK", "SUCCESS")
            if saga_repository:
                saga_repository.save(saga)
            
            # Étape 4: Création de la commande
            self._creer_commande(saga)
            metrics_collector.record_saga_step(saga, "CREATION_COMMANDE", "SUCCESS")
            if saga_repository:
                saga_repository.save(saga)
            
            # Finalisation
            saga.transitionner_vers(
                EtatSaga.SAGA_TERMINEE,
                TypeEvenement.SAGA_TERMINEE_SUCCES,
                message="Saga terminée avec succès"
            )
            
            # Persister l'état final
            if saga_repository:
                saga_repository.save(saga)
            
            # Métriques : saga terminée avec succès
            execution_time = time.time() - start_time
            metrics_collector.record_saga_completed(saga, execution_time)
            
            logger.info(f"Saga {saga.id} terminée avec succès en {execution_time:.2f}s")
            return saga.obtenir_resume_execution()
            
        except Exception as e:
            logger.error(f"Erreur dans la saga {saga.id}: {e}")
            
            # Tenter la compensation si nécessaire
            if saga.necessite_compensation:
                try:
                    self._executer_compensation(saga)
                    if saga_repository:
                        saga_repository.save(saga)
                except Exception as comp_error:
                    logger.error(f"Échec de compensation pour saga {saga.id}: {comp_error}")
            
            # Marquer la saga comme annulée
            if not saga.est_terminee:
                execution_time = time.time() - start_time if 'start_time' in locals() else None
                
                if isinstance(e, StockInsuffisantException):
                    saga.transitionner_vers(
                        EtatSaga.ECHEC_STOCK_INSUFFISANT,
                        TypeEvenement.STOCK_VERIFIE_ECHEC,
                        donnees={"erreur": str(e)},
                        message="Stock insuffisant"
                    )
                    saga.transitionner_vers(
                        EtatSaga.SAGA_ANNULEE,
                        TypeEvenement.COMPENSATION_TERMINEE,
                        message="Saga annulée - stock insuffisant"
                    )
                    # Métriques : échec stock
                    metrics_collector.record_saga_failed(saga, "STOCK_INSUFFISANT", "VERIFICATION_STOCK", execution_time)
                else:
                    # Déterminer l'état d'échec approprié selon l'étape courante
                    etape_echec = self._determiner_etape_echec(e)
                    etat_echec_approprie = self._determiner_etat_echec(saga.etat_actuel, e)
                    
                    # Transitionner vers l'état d'échec approprié d'abord
                    if etat_echec_approprie != saga.etat_actuel:
                        saga.transitionner_vers(
                            etat_echec_approprie,
                            self._determiner_type_evenement_echec(e),
                            donnees={"erreur": str(e)},
                            message=f"Échec lors de {etape_echec}"
                        )
                    
                    # Puis transitionner vers SAGA_ANNULEE selon la machine d'état
                    if etat_echec_approprie in {EtatSaga.ECHEC_STOCK_INSUFFISANT, EtatSaga.ECHEC_RESERVATION_STOCK}:
                        saga.transitionner_vers(
                            EtatSaga.SAGA_ANNULEE,
                            TypeEvenement.COMPENSATION_TERMINEE,
                            message="Saga annulée après échec"
                        )
                    elif etat_echec_approprie == EtatSaga.ECHEC_CREATION_COMMANDE:
                        # Passer par compensation d'abord
                        saga.transitionner_vers(
                            EtatSaga.COMPENSATION_EN_COURS,
                            TypeEvenement.COMPENSATION_DEMANDEE,
                            message="Compensation en cours après échec commande"
                        )
                        saga.transitionner_vers(
                            EtatSaga.SAGA_ANNULEE,
                            TypeEvenement.COMPENSATION_TERMINEE,
                            message="Saga annulée après compensation"
                        )
                    
                    # Métriques : autre échec
                    metrics_collector.record_saga_failed(saga, "ERREUR_TECHNIQUE", etape_echec, execution_time)
                
                # Persister l'état d'échec
                if saga_repository:
                    saga_repository.save(saga)
            
            raise

    def _verifier_stock(self, saga: SagaCommande):
        """Étape 3: Vérification de la disponibilité du stock via l'API stocks-locaux"""
        logger.info(f"Saga {saga.id}: Vérification du stock dans le magasin {saga.magasin_id}")
        
        try:
            # Appel via Kong au service inventaire - récupérer tous les stocks du magasin
            url = f"{self.service_inventaire_url}/api/ddd/inventaire/stocks-locaux/{saga.magasin_id}/"
            
            start_call = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            metrics_collector.record_external_service_call(
                "inventaire", "stocks-locaux", response.status_code, time.time() - start_call
            )
            
            if response.status_code == 404:
                raise ServiceExterneIndisponibleException(
                    "service-inventaire", f"magasin {saga.magasin_id} introuvable"
                )
            elif response.status_code != 200:
                raise ServiceExterneIndisponibleException(
                    "service-inventaire", f"consultation stocks magasin {saga.magasin_id}"
                )
            
            # Analyser les stocks retournés
            stocks_data = response.json()
            stocks_par_produit = {
                stock["produit_id"]: stock 
                for stock in stocks_data.get("stocks", [])
            }
            
            # Vérifier chaque produit de la commande
            for ligne in saga.lignes_commande:
                if ligne.produit_id not in stocks_par_produit:
                    raise StockInsuffisantException(
                        ligne.produit_id, ligne.quantite, 0
                    )
                
                stock_info = stocks_par_produit[ligne.produit_id]
                quantite_disponible = stock_info.get("quantite", 0)
                
                if quantite_disponible < ligne.quantite:
                    raise StockInsuffisantException(
                        ligne.produit_id, ligne.quantite, quantite_disponible
                    )
                
                logger.info(f"Stock OK pour produit {ligne.produit_id} ({stock_info.get('nom_produit', 'N/A')}): {quantite_disponible} >= {ligne.quantite}")
                
            # Transition vers l'état suivant SEULEMENT si toutes les vérifications passent
            saga.transitionner_vers(
                EtatSaga.STOCK_VERIFIE,
                TypeEvenement.STOCK_VERIFIE_SUCCES,
                message="Stock vérifié pour tous les produits"
            )
                
        except requests.RequestException as e:
            raise ServiceExterneIndisponibleException(
                "service-inventaire", f"vérification stocks: {e}"
            )

    def _recuperer_informations_produit(self, saga: SagaCommande):
        """Étape 2: Récupération des informations produit via Kong"""
        logger.info(f"Saga {saga.id}: Récupération informations produit")
        
        # Pas de transition d'état - on reste dans STOCK_VERIFIE
        # La prochaine transition sera vers RESERVATION_STOCK
        
        for ligne in saga.lignes_commande:
            try:
                # Appel via Kong au service catalogue
                url = f"{self.service_catalogue_url}/api/ddd/catalogue/produits/{ligne.produit_id}/"
                
                start_call = time.time()
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                metrics_collector.record_external_service_call(
                    "catalogue", "produits", response.status_code, time.time() - start_call
                )
                
                if response.status_code == 404:
                    raise ServiceExterneIndisponibleException(
                        "service-catalogue", f"produit {ligne.produit_id} introuvable"
                    )
                elif response.status_code != 200:
                    raise ServiceExterneIndisponibleException(
                        "service-catalogue", f"récupération produit {ligne.produit_id}"
                    )
                
                produit_data = response.json()
                
                # Sauvegarder les informations produit pour la commande finale
                if "informations_produits" not in saga.donnees_contexte:
                    saga.donnees_contexte["informations_produits"] = {}
                
                saga.donnees_contexte["informations_produits"][ligne.produit_id] = {
                    "id": produit_data.get("id"),
                    "nom": produit_data.get("nom"),
                    "prix": produit_data.get("prix"),
                    "description": produit_data.get("description"),
                    "categorie": produit_data.get("categorie")
                }
                
                # Mettre à jour la ligne de commande avec les vraies données du catalogue
                ligne.nom_produit = produit_data.get("nom", "")
                ligne.prix_unitaire = float(produit_data.get("prix", 0.0))
                
                logger.info(f"Informations produit récupérées: {produit_data.get('nom')} - {produit_data.get('prix')}€")
                
            except requests.RequestException as e:
                raise ServiceExterneIndisponibleException(
                    "service-catalogue", f"récupération produit: {e}"
                )

    def _reserver_stock(self, saga: SagaCommande):
        """Étape 2: Réservation du stock"""
        logger.info(f"Saga {saga.id}: Réservation du stock")
        
        saga.transitionner_vers(
            EtatSaga.RESERVATION_STOCK,
            TypeEvenement.STOCK_VERIFIE_SUCCES,
            message="Début de la réservation de stock"
        )
        
        reservations_effectuees = []
        
        try:
            for ligne in saga.lignes_commande:
                # Appel au service inventaire pour diminuer le stock
                # IMPORTANT: L'API attend des strings pour les UUIDs (comme dans http_stock_service.py)
                diminuer_data = {
                    "produit_id": str(ligne.produit_id),
                    "quantite": ligne.quantite,
                    "magasin_id": str(saga.magasin_id)
                }
                
                url = f"{self.service_inventaire_url}/api/ddd/inventaire/diminuer-stock/"
                
                start_call = time.time()
                response = requests.post(
                    url,
                    json=diminuer_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                metrics_collector.record_external_service_call(
                    "inventaire", "diminuer-stock", response.status_code, time.time() - start_call
                )
                
                if response.status_code == 400:
                    error_data = response.json()
                    if "insuffisant" in error_data.get("error", "").lower():
                        raise StockInsuffisantException(
                            ligne.produit_id, ligne.quantite, 0
                        )
                    else:
                        raise ReservationStockEchecException(
                            ligne.produit_id, error_data.get("error", "Erreur inconnue")
                        )
                elif response.status_code != 200:
                    raise ServiceExterneIndisponibleException(
                        "service-inventaire", f"réservation stock produit {ligne.produit_id}"
                    )
                
                # Enregistrer l'ID de réservation (ici on utilise produit_id comme clé)
                saga.ajouter_reservation_stock(
                    ligne.produit_id, 
                    f"reservation_{saga.id}_{ligne.produit_id}"
                )
                reservations_effectuees.append(ligne.produit_id)
                
                logger.info(f"Stock réservé pour produit {ligne.produit_id}: {ligne.quantite} unités")
                
        except Exception as e:
            # En cas d'erreur, libérer les réservations déjà effectuées
            self._liberer_reservations_partielles(saga, reservations_effectuees)
            raise
        
        # Transition vers l'état suivant
        saga.transitionner_vers(
            EtatSaga.STOCK_RESERVE,
            TypeEvenement.STOCK_RESERVE_SUCCES,
            donnees={"reservations": list(saga.reservation_stock_ids.values())},
            message=f"Stock réservé pour {len(saga.lignes_commande)} produits"
        )

    def _creer_commande(self, saga: SagaCommande):
        """Étape 3: Création de la commande finale"""
        logger.info(f"Saga {saga.id}: Création de la commande")
        
        saga.transitionner_vers(
            EtatSaga.CREATION_COMMANDE,
            TypeEvenement.STOCK_RESERVE_SUCCES,
            message="Début de la création de commande"
        )
        
        try:
            # Préparer les données pour le service commandes
            commande_data = saga.obtenir_donnees_pour_commande()
            
            # Adapter le format pour l'API du service commandes
            # Puisque l'API existante prend une seule ligne à la fois,
            # nous allons créer une vente avec plusieurs lignes
            vente_data = {
                "magasin_id": str(saga.magasin_id),
                "client_id": str(saga.client_id),
                # On prend la première ligne pour l'API existante
                "produit_id": str(saga.lignes_commande[0].produit_id),
                "quantite": saga.lignes_commande[0].quantite
            }
            
            url = f"{self.service_commandes_url}/api/v1/ventes-ddd/enregistrer/"
            
            start_call = time.time()
            response = requests.post(
                url,
                json=vente_data,
                headers=self.headers,
                timeout=self.timeout
            )
            metrics_collector.record_external_service_call(
                "commandes", "enregistrer", response.status_code, time.time() - start_call
            )
            
            if response.status_code != 201:
                error_data = response.json() if response.content else {}
                raise CreationCommandeEchecException(
                    f"Erreur {response.status_code}: {error_data.get('error', 'Erreur inconnue')}"
                )
            
            commande_result = response.json()
            vente_id = commande_result.get("vente", {}).get("id")
            
            if vente_id:
                saga.commande_finale_id = vente_id
                
            logger.info(f"Commande créée avec succès: {vente_id}")
            
        except requests.RequestException as e:
            raise ServiceExterneIndisponibleException(
                "service-commandes", f"création commande: {e}"
            )
        
        # Transition vers l'état suivant
        saga.transitionner_vers(
            EtatSaga.COMMANDE_CREEE,
            TypeEvenement.COMMANDE_CREEE_SUCCES,
            donnees={"commande_id": saga.commande_finale_id},
            message=f"Commande créée: {saga.commande_finale_id}"
        )

    def _executer_compensation(self, saga: SagaCommande):
        """Exécute les actions de compensation en cas d'échec"""
        logger.warning(f"Saga {saga.id}: Exécution de la compensation")
        
        saga.transitionner_vers(
            EtatSaga.COMPENSATION_EN_COURS,
            TypeEvenement.COMPENSATION_DEMANDEE,
            message="Début de la compensation"
        )
        
        # Libérer les réservations de stock
        if saga.reservation_stock_ids:
            self._liberer_stock_reserve(saga)
        
        saga.transitionner_vers(
            EtatSaga.SAGA_ANNULEE,
            TypeEvenement.COMPENSATION_TERMINEE,
            message="Compensation terminée, saga annulée"
        )

    def _liberer_stock_reserve(self, saga: SagaCommande):
        """Libère le stock réservé en cas de compensation"""
        logger.info(f"Saga {saga.id}: Libération du stock réservé")
        
        for ligne in saga.lignes_commande:
            if ligne.produit_id in saga.reservation_stock_ids:
                try:
                    # Remettre le stock en augmentant la quantité
                    augmenter_data = {
                        "produit_id": ligne.produit_id,
                        "quantite": ligne.quantite,
                        "magasin_id": saga.magasin_id
                    }
                    
                    url = f"{self.service_inventaire_url}/api/ddd/inventaire/augmenter-stock/"
                    
                    response = requests.post(
                        url,
                        json=augmenter_data,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Stock libéré pour produit {ligne.produit_id}: {ligne.quantite} unités")
                    else:
                        logger.error(f"Échec libération stock produit {ligne.produit_id}: {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.error(f"Erreur réseau lors de la libération stock {ligne.produit_id}: {e}")

    def _liberer_reservations_partielles(self, saga: SagaCommande, produits_a_liberer: List[int]):
        """Libère les réservations partielles en cas d'échec de réservation"""
        logger.warning(f"Saga {saga.id}: Libération des réservations partielles")
        
        for ligne in saga.lignes_commande:
            if ligne.produit_id in produits_a_liberer:
                try:
                    augmenter_data = {
                        "produit_id": ligne.produit_id,
                        "quantite": ligne.quantite,
                        "magasin_id": saga.magasin_id
                    }
                    
                    url = f"{self.service_inventaire_url}/api/ddd/inventaire/augmenter-stock/"
                    
                    requests.post(
                        url,
                        json=augmenter_data,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la libération partielle du produit {ligne.produit_id}: {e}")

    def _determiner_etape_echec(self, exception: Exception) -> str:
        """Détermine l'étape où l'échec s'est produit"""
        if isinstance(exception, StockInsuffisantException):
            return "VERIFICATION_STOCK"
        elif isinstance(exception, ReservationStockEchecException):
            return "RESERVATION_STOCK"
        elif isinstance(exception, CreationCommandeEchecException):
            return "CREATION_COMMANDE"
        elif isinstance(exception, ServiceExterneIndisponibleException):
            return "SERVICE_EXTERNE"
        else:
            return "INCONNUE"
    
    def _determiner_etat_echec(self, etat_actuel: EtatSaga, exception: Exception) -> EtatSaga:
        """Détermine l'état d'échec approprié selon l'état actuel et l'exception"""
        if isinstance(exception, StockInsuffisantException):
            return EtatSaga.ECHEC_STOCK_INSUFFISANT
        elif isinstance(exception, ReservationStockEchecException):
            return EtatSaga.ECHEC_RESERVATION_STOCK
        elif isinstance(exception, CreationCommandeEchecException):
            return EtatSaga.ECHEC_CREATION_COMMANDE
        else:
            # Pour les autres erreurs, déterminer selon l'état actuel
            if etat_actuel in {EtatSaga.EN_ATTENTE, EtatSaga.VERIFICATION_STOCK, EtatSaga.STOCK_VERIFIE}:
                return EtatSaga.ECHEC_STOCK_INSUFFISANT  # Erreur générique au niveau stock
            elif etat_actuel in {EtatSaga.RESERVATION_STOCK, EtatSaga.STOCK_RESERVE}:
                return EtatSaga.ECHEC_RESERVATION_STOCK
            elif etat_actuel in {EtatSaga.CREATION_COMMANDE, EtatSaga.COMMANDE_CREEE}:
                return EtatSaga.ECHEC_CREATION_COMMANDE
            else:
                return EtatSaga.ECHEC_STOCK_INSUFFISANT  # Fallback
    
    def _determiner_type_evenement_echec(self, exception: Exception) -> TypeEvenement:
        """Détermine le type d'événement d'échec approprié"""
        if isinstance(exception, StockInsuffisantException):
            return TypeEvenement.STOCK_VERIFIE_ECHEC
        elif isinstance(exception, ReservationStockEchecException):
            return TypeEvenement.STOCK_RESERVE_ECHEC
        elif isinstance(exception, CreationCommandeEchecException):
            return TypeEvenement.COMMANDE_CREEE_ECHEC
        else:
            return TypeEvenement.STOCK_VERIFIE_ECHEC  # Fallback

    def obtenir_statut_saga(self, saga_id: str) -> Dict[str, Any]:
        """
        Obtient le statut actuel d'une saga
        (Méthode pour consultation, à implémenter avec un repository)
        """
        # TODO: Implémenter avec un SagaRepository
        return {
            "saga_id": saga_id,
            "message": "Consultation de statut à implémenter avec persistance"
        } 