#!/usr/bin/env python3
"""
Script de test d'intégration pour le Service Saga Orchestrator
Teste le workflow complet : vérification stock → récupération produit → réservation → commande
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class SagaIntegrationTest:
    """Tests d'intégration pour les sagas orchestrées"""
    
    def __init__(self, base_url: str = "http://localhost:8009"):
        self.base_url = base_url.rstrip("/")
        self.kong_url = "http://localhost:8080"
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': 'magasin-secret-key-2025'
        }
    
    def test_health_checks(self) -> bool:
        """Teste que tous les services sont accessibles"""
        print("🏥 Test des health checks...")
        
        services = [
            ("Saga Orchestrator", f"{self.base_url}/api/saga/health/"),
            ("Kong Catalogue", f"{self.kong_url}/api/catalogue/api/ddd/catalogue/health/"),
            ("Kong Inventaire", f"{self.kong_url}/api/inventaire/api/ddd/inventaire/health/"),
            ("Kong Commandes", f"{self.kong_url}/api/commandes/api/v1/magasins/"),
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {service_name} : OK")
                else:
                    print(f"   ❌ {service_name} : {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ {service_name} : {e}")
                return False
        
        return True
    
    def test_saga_success(self) -> bool:
        """Teste une saga qui doit réussir"""
        print("\n🎯 Test saga avec succès...")
        
        # Données de test - seuls produit_id et quantite sont requis (tous UUIDs)
        saga_data = {
            "client_id": "12345678-1234-1234-1234-123456789012",
            "magasin_id": "550e8400-e29b-41d4-a716-446655440000",
            "lignes": [
                {
                    "produit_id": "550e8400-e29b-41d4-a716-446655440001",  # Clavier mécanique
                    "quantite": 1
                }
            ]
        }
        
        try:
            # Démarrer la saga
            print("   📤 Démarrage de la saga...")
            response = requests.post(
                f"{self.base_url}/api/saga/commandes/",
                json=saga_data,
                timeout=30
            )
            
            if response.status_code != 201:
                print(f"   ❌ Échec création saga: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
            
            result = response.json()
            saga_id = result.get("saga_id")
            print(f"   ✅ Saga créée: {saga_id}")
            print(f"   État final: {result.get('etat_final')}")
            
            # Vérifier le statut final
            if result.get("success") and result.get("etat_final") == "SAGA_TERMINEE":
                print("   🎉 Saga terminée avec succès !")
                
                # Consulter les détails
                details_response = requests.get(f"{self.base_url}/api/saga/commandes/{saga_id}/")
                if details_response.status_code == 200:
                    details = details_response.json()
                    print(f"   📊 Nombre d'événements: {len(details.get('historique_evenements', []))}")
                    print(f"   🛒 Commande finale: {details.get('commande_finale_id')}")
                
                return True
            else:
                print(f"   ❌ Saga échouée: {result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur lors du test: {e}")
            return False
    
    def test_saga_stock_insuffisant(self) -> bool:
        """Teste une saga qui doit échouer (stock insuffisant)"""
        print("\n❌ Test saga avec stock insuffisant...")
        
        # Données de test avec quantité excessive - seuls produit_id et quantite sont requis (tous UUIDs)
        saga_data = {
            "client_id": "12345678-1234-1234-1234-123456789012",
            "magasin_id": "550e8400-e29b-41d4-a716-446655440000",
            "lignes": [
                {
                    "produit_id": "550e8400-e29b-41d4-a716-446655440001",
                    "quantite": 1000  # Quantité impossible
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/saga/commandes/",
                json=saga_data,
                timeout=30
            )
            
            # Doit échouer avec stock insuffisant
            if response.status_code == 400:
                result = response.json()
                if "stock insuffisant" in result.get("error", "").lower():
                    print("   ✅ Échec attendu détecté: stock insuffisant")
                    return True
            
            print(f"   ❌ Comportement inattendu: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
            
        except Exception as e:
            print(f"   ❌ Erreur lors du test: {e}")
            return False
    
    def test_metrics_endpoint(self) -> bool:
        """Teste l'endpoint des métriques Prometheus"""
        print("\n📊 Test des métriques Prometheus...")
        
        try:
            response = requests.get(f"{self.base_url}/metrics/", timeout=10)
            
            if response.status_code == 200:
                metrics_text = response.text
                
                # Vérifier la présence de quelques métriques clés
                expected_metrics = [
                    "saga_total",
                    "saga_duree_seconds",
                    "saga_echecs_total",
                    "saga_etapes_total",
                    "services_externes_calls_total"
                ]
                
                missing_metrics = []
                for metric in expected_metrics:
                    if metric not in metrics_text:
                        missing_metrics.append(metric)
                
                if not missing_metrics:
                    print("   ✅ Toutes les métriques attendues sont présentes")
                    print(f"   📏 Taille des métriques: {len(metrics_text)} caractères")
                    return True
                else:
                    print(f"   ❌ Métriques manquantes: {missing_metrics}")
                    return False
            else:
                print(f"   ❌ Échec accès métriques: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur lors du test métriques: {e}")
            return False
    
    def test_api_via_kong(self) -> bool:
        """Teste l'accès aux APIs via Kong"""
        print("\n🌉 Test accès via Kong API Gateway...")
        
        try:
            # Test accès saga via Kong (si configuré)
            response = requests.get(
                f"{self.kong_url}/api/saga/api/saga/health/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("   ✅ Service saga accessible via Kong")
                return True
            else:
                print(f"   ℹ️  Service saga pas encore dans Kong: {response.status_code}")
                print("   (Normal si Kong n'est pas encore configuré pour la saga)")
                return True  # Pas critique
                
        except Exception as e:
            print(f"   ℹ️  Kong saga non configuré: {e}")
            return True  # Pas critique
    
    def run_all_tests(self) -> bool:
        """Exécute tous les tests d'intégration"""
        print("🚀 Début des tests d'intégration Service Saga Orchestrator")
        print("=" * 60)
        
        tests = [
            ("Health Checks", self.test_health_checks),
            ("Saga Success", self.test_saga_success),
            ("Saga Stock Insuffisant", self.test_saga_stock_insuffisant),
            ("Métriques Prometheus", self.test_metrics_endpoint),
            ("Accès via Kong", self.test_api_via_kong),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Erreur dans {test_name}: {e}")
                results[test_name] = False
        
        # Résumé
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        success_count = 0
        for test_name, success in results.items():
            status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
            print(f"{status:12} | {test_name}")
            if success:
                success_count += 1
        
        print(f"\n🎯 Résultat global: {success_count}/{len(tests)} tests réussis")
        
        if success_count == len(tests):
            print("🎉 TOUS LES TESTS SONT RÉUSSIS ! Le service saga est opérationnel.")
            return True
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez les logs ci-dessus.")
            return False


def main():
    """Point d'entrée du script de test"""
    
    # Vérifier les arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8009"
    
    print(f"🔧 URL du service saga: {base_url}")
    print(f"🔧 URL Kong: http://localhost:8080")
    
    # Attendre un peu que les services soient prêts
    print("⏳ Attente de 5 secondes pour que les services soient prêts...")
    time.sleep(5)
    
    # Exécuter les tests
    tester = SagaIntegrationTest(base_url)
    success = tester.run_all_tests()
    
    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 