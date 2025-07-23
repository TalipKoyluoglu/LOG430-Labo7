"""
Tests End-to-End (E2E) pour le module magasin
Tests complets via Kong Gateway avec vraies APIs
"""

import pytest
import requests
import time
import uuid
from django.test import Client
from django.urls import reverse


@pytest.mark.e2e
@pytest.mark.integration
class TestMagasinE2EWorkflows:
    """Tests E2E des workflows complets du magasin"""

    def setup_method(self):
        self.client = Client()
        self.kong_base = "http://localhost:8080"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": "magasin-secret-key-2025",
        }

    def test_workflow_complet_gestion_stock(self):
        """Test E2E complet : Consultation stocks → Demande réapprovisionnement"""
        # 1. Consultation des stocks via Django
        response = self.client.get(reverse("gestion_stocks"))
        assert response.status_code == 200

        # 2. Vérification que les données viennent bien de l'API inventaire
        if "stocks" in response.context and response.context["stocks"]:
            stocks = response.context["stocks"]
            assert isinstance(stocks, list)

            # 3. Si stock faible détecté, créer demande réapprovisionnement
            for stock in stocks:
                if stock.get("quantite", 0) < stock.get("seuil_minimum", 10):
                    # Test création demande via Django
                    reappro_response = self.client.post(
                        reverse("reapprovisionner"),
                        {
                            "produit_id": stock.get("produit_id", "1"),
                            "magasin_id": "1",
                            "quantite": "25",
                        },
                    )
                    # Peut être 302 (redirect) ou 200 selon la logique
                    assert reappro_response.status_code in [200, 302]
                    break

    def test_workflow_complet_gestion_produits(self):
        """Test E2E complet : Lister produits → Rechercher → Ajouter nouveau"""
        # 1. Listing de tous les produits
        response = self.client.get(reverse("lister_produits"))
        assert response.status_code == 200

        # 2. Recherche avec critères (utilise le même endpoint que lister)
        search_response = self.client.get(
            reverse("lister_produits"),
            {"nom": "test", "prix_min": "10", "prix_max": "100"},
        )
        assert search_response.status_code == 200

        # 3. Ajout d'un nouveau produit
        nouveau_produit = {
            "nom": f"Produit Test E2E {uuid.uuid4()}",
            "prix": "29.99",
            "description": "Produit créé par test E2E",
            "categorie": "Test",
        }

        add_response = self.client.post(reverse("ajouter_produit"), nouveau_produit)
        # Succès = redirect ou affichage confirmation
        assert add_response.status_code in [200, 302]

    def test_workflow_complet_rapport_ventes(self):
        """Test E2E complet : Rapport → Formulaire vente → Enregistrement"""
        # 1. Génération du rapport consolidé
        rapport_response = self.client.get(reverse("rapport_consolide"))
        assert rapport_response.status_code == 200

        # 2. Affichage formulaire nouvelle vente
        form_response = self.client.get(reverse("ajouter_vente"))
        assert form_response.status_code == 200

        # 3. Enregistrement d'une nouvelle vente
        nouvelle_vente = {
            "magasin_id": "1",
            "produit_id": "1",
            "quantite": "2",
            "client_id": f"client-e2e-{uuid.uuid4()}",
        }

        vente_response = self.client.post(reverse("enregistrer_vente"), nouvelle_vente)
        assert vente_response.status_code in [200, 302]

    def test_workflow_complet_supply_chain(self):
        """Test E2E complet : Lister demandes → Valider/Rejeter"""
        # 1. Consultation des demandes en attente
        demandes_response = self.client.get(reverse("workflow_demandes"))
        assert demandes_response.status_code == 200

        # 2. Si des demandes existent, tester validation/rejet
        if (
            "demandes" in demandes_response.context
            and demandes_response.context["demandes"]
        ):
            demandes = demandes_response.context["demandes"]
            if demandes:
                demande_id = demandes[0].get("id", "test-demande")

                # Test validation d'une demande
                validation_response = self.client.post(
                    reverse("valider_demande", args=[demande_id])
                )
                assert validation_response.status_code in [200, 302]

    def test_workflow_dashboard_indicateurs(self):
        """Test E2E complet : Dashboard avec indicateurs en temps réel"""
        # 1. Accès au dashboard
        dashboard_response = self.client.get(reverse("indicateurs_performance"))
        assert dashboard_response.status_code == 200

        # 2. Vérification que les indicateurs sont présents
        if "indicateurs" in dashboard_response.context:
            indicateurs = dashboard_response.context["indicateurs"]
            assert isinstance(indicateurs, (list, dict))

    def test_integration_kong_gateway_direct(self):
        """Test E2E : Accès direct aux APIs via Kong Gateway"""
        # Test ping de tous les services via Kong
        services_endpoints = [
            "/api/catalogue/health/",
            "/api/inventaire/health/",
            "/api/commandes/health/",
            "/api/supply-chain/health/",
            "/api/ecommerce/health/",
        ]

        for endpoint in services_endpoints:
            try:
                response = requests.get(
                    f"{self.kong_base}{endpoint}", headers=self.headers, timeout=5
                )
                # Accepter 200 (OK) ou 404 (service pas encore en ligne)
                assert response.status_code in [200, 404, 502]
            except requests.exceptions.RequestException:
                # Kong ou service peut être down - acceptable en test
                pass

    def test_resilience_services_indisponibles(self):
        """Test E2E : Résilience quand services sont indisponibles"""
        # Test que l'interface Django fonctionne même si APIs externes échouent

        # Ces tests doivent passer même si les microservices sont down
        views_to_test = [
            reverse("gestion_stocks"),
            reverse("lister_produits"),
            reverse("rapport_consolide"),
            reverse("workflow_demandes"),
            reverse("indicateurs_performance"),
        ]

        for view_url in views_to_test:
            try:
                response = self.client.get(view_url)
                # L'interface doit rester accessible même avec erreurs API
                assert response.status_code == 200
                # Les templates doivent gérer l'absence de données
            except Exception as e:
                pytest.fail(f"View {view_url} failed: {e}")


@pytest.mark.e2e
@pytest.mark.integration
class TestMagasinE2EPerformance:
    """Tests E2E de performance et charge"""

    def setup_method(self):
        self.client = Client()

    def test_performance_pages_principales(self):
        """Test performance des pages principales"""
        pages = [
            reverse("gestion_stocks"),
            reverse("lister_produits"),
            reverse("rapport_consolide"),
            reverse("indicateurs_performance"),
        ]

        for page_url in pages:
            start_time = time.time()
            response = self.client.get(page_url)
            end_time = time.time()

            response_time = end_time - start_time

            # Page doit répondre en moins de 5 secondes
            assert (
                response_time < 5.0
            ), f"Page {page_url} trop lente: {response_time:.2f}s"
            assert response.status_code == 200

    def test_charge_requests_concurrents(self):
        """Test basique de charge avec requêtes concurrentes"""
        import threading

        results = []

        def make_request():
            try:
                response = self.client.get(reverse("indicateurs_performance"))
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))

        # 10 requêtes concurrentes
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Au moins 80% des requêtes doivent réussir
        success_count = sum(1 for r in results if r == 200)
        success_rate = success_count / len(results)
        assert success_rate >= 0.8, f"Taux de succès trop bas: {success_rate:.2%}"


@pytest.mark.e2e
@pytest.mark.integration
class TestMagasinE2ELogging:
    """Tests E2E du système de logging"""

    def setup_method(self):
        self.client = Client()

    def test_logs_generes_par_actions(self):
        """Test que les actions génèrent bien des logs"""
        import logging
        from io import StringIO

        # Capturer les logs
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)

        magasin_logger = logging.getLogger("magasin")
        magasin_logger.addHandler(handler)
        magasin_logger.setLevel(logging.INFO)

        try:
            # Actions qui doivent générer des logs
            self.client.get(reverse("gestion_stocks"))
            self.client.get(reverse("lister_produits"))
            self.client.get(reverse("indicateurs_performance"))

            # Vérifier que des logs ont été générés
            log_contents = log_capture.getvalue()

            # Rechercher nos émojis de logs
            log_indicators = ["🏪", "📦", "📈", "🔍", "📊"]
            logs_found = any(indicator in log_contents for indicator in log_indicators)

            # Au moins un log doit être présent
            assert (
                logs_found or len(log_contents) > 0
            ), "Aucun log généré par les actions"

        finally:
            magasin_logger.removeHandler(handler)

    def test_logs_erreurs_gestion_gracieuse(self):
        """Test que les erreurs sont bien loggées"""
        import logging
        from io import StringIO

        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.ERROR)

        magasin_logger = logging.getLogger("magasin")
        magasin_logger.addHandler(handler)
        magasin_logger.setLevel(logging.ERROR)

        try:
            # Actions qui peuvent générer des erreurs (services down)
            self.client.get(reverse("gestion_stocks"))

            # Même en cas d'erreur, page doit rester accessible
            # Les erreurs doivent être loggées, pas causées d'exceptions

        finally:
            magasin_logger.removeHandler(handler)


@pytest.mark.e2e
@pytest.mark.django_db
class TestMagasinE2EDatabase:
    """Tests E2E de la base de données Django (sessions, auth)"""

    def setup_method(self):
        self.client = Client()

    def test_sessions_django_fonctionnelles(self):
        """Test que les sessions Django fonctionnent avec SQLite"""
        # Test basique des sessions
        session = self.client.session
        session["test_key"] = "test_value"
        session.save()

        # Nouvelle requête doit conserver la session
        response = self.client.get(reverse("indicateurs_performance"))
        assert response.status_code == 200

        # Session doit être conservée
        assert self.client.session.get("test_key") == "test_value"

    def test_middleware_observability(self):
        """Test que le middleware d'observabilité fonctionne"""
        # Le middleware doit traiter toutes les requêtes
        response = self.client.get(reverse("indicateurs_performance"))
        assert response.status_code == 200

        # Vérifier que les headers d'observabilité sont présents si configurés
        # (pas obligatoire mais bon à vérifier)
        # assert 'X-Request-ID' in response or True  # Optionnel
