"""
Configuration pytest pour tests d'intégration microservices DDD
Tests via Kong Gateway - Environnement Docker
"""

import os

# Force SQLite usage for integration tests to avoid PostgreSQL connection issues
# MUST be set before Django imports
os.environ.setdefault("DATABASE_URL", "sqlite:///test_db.sqlite3")

import pytest
import requests
import time
import uuid
from typing import Dict, Any, Optional

# Configuration Kong Gateway (Tests d'intégration)
KONG_GATEWAY_URL = "http://localhost:8080"
KONG_ADMIN_URL = "http://localhost:8081"
API_KEY = "magasin-secret-key-2025"

# Headers standards pour tous les appels Kong
KONG_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-API-Key": API_KEY,
}


@pytest.fixture(scope="session")
def kong_client():
    """Client HTTP configuré pour Kong Gateway"""
    session = requests.Session()
    session.headers.update(KONG_HEADERS)
    return session


@pytest.fixture(scope="session")
def wait_for_services():
    """Attendre que tous les services soient prêts"""
    services_to_check = [
        f"{KONG_GATEWAY_URL}/api/catalogue/api/ddd/catalogue/health/",
        f"{KONG_GATEWAY_URL}/api/inventaire/health/",
        f"{KONG_GATEWAY_URL}/api/commandes/health/",
        f"{KONG_GATEWAY_URL}/api/supply-chain/health/",
        f"{KONG_GATEWAY_URL}/api/ecommerce/health/",
    ]

    max_retries = 30
    for service_url in services_to_check:
        for retry in range(max_retries):
            try:
                response = requests.get(service_url, headers=KONG_HEADERS, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Service ready: {service_url}")
                    break
            except requests.exceptions.RequestException:
                if retry == max_retries - 1:
                    pytest.fail(
                        f"❌ Service not ready after {max_retries} retries: {service_url}"
                    )
                time.sleep(2)


@pytest.fixture
def test_client_data():
    """Données de test pour création client e-commerce"""
    return {
        "prenom": "Test",
        "nom": "Integration",
        "email": f"test-{uuid.uuid4()}@integration.com",
        "adresse_rue": "123 Rue de Test",
        "adresse_ville": "Montreal",
        "adresse_code_postal": "H1A 1A1",
        "adresse_province": "Quebec",
        "adresse_pays": "Canada",
    }


@pytest.fixture
def test_produit_data():
    """Données de test pour produit catalogue"""
    return {
        "nom": f"Produit Test {uuid.uuid4()}",
        "prix": 99.99,
        "description": "Produit de test pour intégration",
        "categorie": "Test",
    }


@pytest.fixture
def cleanup_test_data():
    """Nettoyage des données de test après chaque test"""
    created_resources = []

    def track_resource(
        resource_type: str, resource_id: str, cleanup_url: Optional[str] = None
    ):
        created_resources.append(
            {"type": resource_type, "id": resource_id, "cleanup_url": cleanup_url}
        )

    yield track_resource

    # Nettoyage après le test (si nécessaire)
    for resource in created_resources:
        try:
            cleanup_url = resource["cleanup_url"]
            if cleanup_url:
                requests.delete(cleanup_url, headers=KONG_HEADERS)
        except Exception as e:
            print(f"⚠️ Cleanup failed for {resource['type']} {resource['id']}: {e}")


def assert_response_success(response: requests.Response, expected_status: int = 200):
    """Helper pour vérifier les réponses HTTP"""
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )


def assert_kong_load_balancing(responses: list, num_instances: int = 3):
    """Helper pour vérifier la distribution load balancing Kong"""
    # Extraire les instance IDs des headers ou réponses
    instance_ids = []
    for response in responses:
        # Récupérer l'instance ID des headers Kong ou du contenu
        instance_id = response.headers.get("X-Instance-ID", "unknown")
        instance_ids.append(instance_id)

    from collections import Counter

    distribution = Counter(instance_ids)

    # Vérifier distribution équitable (±1 requête)
    requests_per_instance = len(responses) // num_instances
    tolerance = 1

    for instance, count in distribution.items():
        assert (
            (requests_per_instance - tolerance)
            <= count
            <= (requests_per_instance + tolerance)
        ), (
            f"Instance {instance} received {count} requests, "
            f"expected {requests_per_instance}±{tolerance}"
        )
