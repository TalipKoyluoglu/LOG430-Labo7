"""
Métriques Prometheus pour l'observabilité des Sagas
Implémente les métriques demandées dans le laboratoire 6
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from typing import Dict, Any
from domain.entities import EtatSaga, SagaCommande

# Métriques pour les sagas
saga_total_counter = Counter(
    'saga_total', 
    'Nombre total de sagas démarrées',
    ['client_type', 'magasin']
)

saga_duree_histogram = Histogram(
    'saga_duree_seconds',
    'Durée d\'exécution des sagas en secondes',
    ['etat_final', 'magasin'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

saga_echecs_counter = Counter(
    'saga_echecs_total',
    'Nombre total d\'échecs de sagas',
    ['type_echec', 'etape_echec', 'magasin']
)

saga_etapes_counter = Counter(
    'saga_etapes_total',
    'Nombre d\'étapes atteintes par les sagas',
    ['etape', 'statut', 'magasin']
)

saga_compensations_counter = Counter(
    'saga_compensations_total',
    'Nombre de compensations exécutées',
    ['type_compensation', 'magasin']
)

# Métriques d'état actuel
saga_actives_gauge = Gauge(
    'saga_actives_current',
    'Nombre de sagas actuellement actives',
    ['etat']
)

saga_info = Info(
    'saga_orchestrator_info',
    'Informations sur le service saga orchestrator'
)

# Métriques des services externes
services_externes_calls_counter = Counter(
    'services_externes_calls_total',
    'Nombre d\'appels aux services externes',
    ['service', 'endpoint', 'status_code']
)

services_externes_duree_histogram = Histogram(
    'services_externes_duree_seconds',
    'Durée des appels aux services externes',
    ['service', 'endpoint'],
    buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)


class SagaMetricsCollector:
    """
    Collecteur de métriques pour les sagas
    """
    
    def __init__(self):
        # Initialiser les informations du service
        saga_info.info({
            'version': '1.0.0',
            'architecture': 'DDD',
            'pattern': 'saga-orchestree-synchrone',
            'services_integres': 'catalogue,inventaire,commandes',
            'communication': 'kong-api-gateway'
        })
    
    def record_saga_started(self, saga: SagaCommande):
        """Enregistre le démarrage d'une saga"""
        saga_total_counter.labels(
            client_type='standard',
            magasin=str(saga.magasin_id)
        ).inc()
        
        saga_etapes_counter.labels(
            etape='DEMARRAGE',
            statut='SUCCESS',
            magasin=str(saga.magasin_id)
        ).inc()
    
    def record_saga_step(self, saga: SagaCommande, etape: str, statut: str):
        """Enregistre une étape de saga"""
        saga_etapes_counter.labels(
            etape=etape,
            statut=statut,
            magasin=str(saga.magasin_id)
        ).inc()
    
    def record_saga_completed(self, saga: SagaCommande, duree_seconds: float):
        """Enregistre la fin d'une saga avec succès"""
        saga_duree_histogram.labels(
            etat_final=saga.etat_actuel.value,
            magasin=str(saga.magasin_id)
        ).observe(duree_seconds)
        
        saga_etapes_counter.labels(
            etape='COMPLETION',
            statut='SUCCESS',
            magasin=str(saga.magasin_id)
        ).inc()
    
    def record_saga_failed(self, saga: SagaCommande, type_echec: str, etape_echec: str, duree_seconds: float = None):
        """Enregistre l'échec d'une saga"""
        saga_echecs_counter.labels(
            type_echec=type_echec,
            etape_echec=etape_echec,
            magasin=str(saga.magasin_id)
        ).inc()
        
        if duree_seconds is not None:
            saga_duree_histogram.labels(
                etat_final=saga.etat_actuel.value,
                magasin=str(saga.magasin_id)
            ).observe(duree_seconds)
        
        saga_etapes_counter.labels(
            etape=etape_echec,
            statut='FAILURE',
            magasin=str(saga.magasin_id)
        ).inc()
    
    def record_compensation(self, saga: SagaCommande, type_compensation: str):
        """Enregistre une compensation"""
        saga_compensations_counter.labels(
            type_compensation=type_compensation,
            magasin=str(saga.magasin_id)
        ).inc()
    
    def record_external_service_call(self, service: str, endpoint: str, status_code: int, duree_seconds: float):
        """Enregistre un appel à un service externe"""
        services_externes_calls_counter.labels(
            service=service,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        services_externes_duree_histogram.labels(
            service=service,
            endpoint=endpoint
        ).observe(duree_seconds)
    
    def update_active_sagas_count(self, sagas_by_state: Dict[str, int]):
        """Met à jour le nombre de sagas actives par état"""
        for etat, count in sagas_by_state.items():
            saga_actives_gauge.labels(etat=etat).set(count)


class MetricsDecorator:
    """
    Décorateur pour automatiser la collecte de métriques
    """
    
    def __init__(self, metrics_collector: SagaMetricsCollector):
        self.metrics = metrics_collector
    
    def time_external_call(self, service: str, endpoint: str):
        """Décorateur pour mesurer les appels externes"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    # Supposer que result a un status_code
                    status_code = getattr(result, 'status_code', 200)
                    self.metrics.record_external_service_call(
                        service, endpoint, status_code, time.time() - start_time
                    )
                    return result
                except Exception as e:
                    self.metrics.record_external_service_call(
                        service, endpoint, 500, time.time() - start_time
                    )
                    raise
            return wrapper
        return decorator


# Instance globale du collecteur de métriques
metrics_collector = SagaMetricsCollector() 