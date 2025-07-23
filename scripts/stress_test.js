import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

// Métriques personnalisées
const errorRate = new Rate('errors');

// Configuration du test de stress
export const options = {
  stages: [
    // Phase de montée en charge progressive jusqu'à l'effondrement
    { duration: '1m', target: 10 },   // 0 à 10 utilisateurs
    { duration: '2m', target: 25 },   // 10 à 25 utilisateurs
    { duration: '2m', target: 50 },   // 25 à 50 utilisateurs
    { duration: '2m', target: 100 },  // 50 à 100 utilisateurs
    { duration: '2m', target: 150 },  // 100 à 150 utilisateurs
    { duration: '2m', target: 200 },  // 150 à 200 utilisateurs
    { duration: '3m', target: 200 },  // Maintenir 200 utilisateurs
    { duration: '1m', target: 0 },    // Redescendre à 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% des requêtes < 5s (plus permissif)
    http_req_failed: ['rate<0.3'],     // Taux d'erreur < 30% (plus permissif)
    errors: ['rate<0.3'],              // Taux d'erreur personnalisé < 30%
  },
};

// Configuration des paramètres du test
// L'URL de base pointe maintenant vers le port 80, où NGINX écoute.
const BASE_URL = 'http://localhost:80';
const AUTH_TOKEN = '067642733604a8497645e9214d02641a14f44ed2'; // Remplacez par un token valide

// Headers communs
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Token ${AUTH_TOKEN}`,
};

// Configuration du nom du fichier de résultats
// Important : Le nom du fichier inclut maintenant un suffixe pour indiquer
// que ce test est réalisé "après" la mise en place du load balancer (lb).
const TEST_NAME = "stress_test_3_instances_after_lb";
const results_file = `results/${TEST_NAME}_${new Date().toISOString().slice(0, 19).replace(/[:]/g, "")}.json`;

// Fonction principale du test de stress
export default function () {
  const group = __VU % 4; // Répartir en 4 groupes pour plus de variété

  switch (group) {
    case 0:
      // Groupe 1: Consultation intensive des stocks
      testIntensiveStockConsultation();
      break;
    case 1:
      // Groupe 2: Génération intensive de rapports
      testIntensiveReportsGeneration();
      break;
    case 2:
      // Groupe 3: Mise à jour intensive de produits
      testIntensiveProductUpdates();
      break;
    case 3:
      // Groupe 4: Requêtes mixtes intensives
      testMixedIntensiveRequests();
      break;
  }

  sleep(0.5); // Pause plus courte pour plus de stress
}

// Test 1: Consultation intensive des stocks
function testIntensiveStockConsultation() {
  const storeIds = [1, 2, 3, 4, 5];
  const storeId = storeIds[__VU % storeIds.length];
  
  // Test endpoint stock simple
  const stockResponse = http.get(`${BASE_URL}/api/v1/stores/${storeId}/stock/`);
  check(stockResponse, {
    'stock consultation status is 200': (r) => r.status === 200,
  });
  
  // Test endpoint stock avec pagination et filtrage
  const stockListResponse = http.get(
    `${BASE_URL}/api/v1/stores/${storeId}/stock/list/?page=1&ordering=-quantite`
  );
  check(stockListResponse, {
    'stock list status is 200': (r) => r.status === 200,
  });
  
  // Test avec filtrage complexe
  const filteredResponse = http.get(
    `${BASE_URL}/api/v1/stores/${storeId}/stock/list/?produit__nom=Café&quantite__gte=10&ordering=produit__nom`
  );
  check(filteredResponse, {
    'filtered stock status is 200': (r) => r.status === 200,
  });
  
  if (stockResponse.status !== 200 || stockListResponse.status !== 200 || filteredResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Test 2: Génération intensive de rapports
function testIntensiveReportsGeneration() {
  // Test rapport des ventes
  const reportsResponse = http.get(`${BASE_URL}/api/v1/reports/`);
  check(reportsResponse, {
    'reports status is 200': (r) => r.status === 200,
  });
  
  // Test dashboard performances
  const dashboardResponse = http.get(`${BASE_URL}/api/v1/dashboard/`);
  check(dashboardResponse, {
    'dashboard status is 200': (r) => r.status === 200,
  });
  
  // Test avec paramètres de date (si supporté)
  const reportsWithParams = http.get(`${BASE_URL}/api/v1/reports/?date=2024-01-01`);
  check(reportsWithParams, {
    'reports with params status is 200': (r) => r.status === 200,
  });
  
  if (reportsResponse.status !== 200 || dashboardResponse.status !== 200 || reportsWithParams.status !== 200) {
    errorRate.add(1);
  }
}

// Test 3: Mise à jour intensive de produits
function testIntensiveProductUpdates() {
  const productIds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  const productId = productIds[__VU % productIds.length];
  
  // Données de mise à jour
  const updateData = {
    nom: `Produit Stress Test - VU${__VU} - ${Date.now()}`,
    prix: 15.99 + (__VU * 0.1) + (Math.random() * 10),
    description: `Description stress test par VU ${__VU} - ${Date.now()}`,
  };
  
  const updateResponse = http.put(
    `${BASE_URL}/api/v1/products/${productId}/`,
    JSON.stringify(updateData),
    { headers }
  );
  
  check(updateResponse, {
    'product update status is 200': (r) => r.status === 200,
  });
  
  // Test de lecture après mise à jour
  const readResponse = http.get(`${BASE_URL}/api/v1/products/${productId}/`);
  check(readResponse, {
    'product read after update status is 200': (r) => r.status === 200,
  });
  
  if (updateResponse.status !== 200 || readResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Test 4: Requêtes mixtes intensives
function testMixedIntensiveRequests() {
  const storeId = (__VU % 3) + 1;
  const productId = (__VU % 5) + 1;
  
  // Requête 1: Stock
  const stockResponse = http.get(`${BASE_URL}/api/v1/stores/${storeId}/stock/`);
  
  // Requête 2: Rapport
  const reportsResponse = http.get(`${BASE_URL}/api/v1/reports/`);
  
  // Requête 3: Produit
  const productResponse = http.get(`${BASE_URL}/api/v1/products/${productId}/`);
  
  // Requête 4: Dashboard
  const dashboardResponse = http.get(`${BASE_URL}/api/v1/dashboard/`);
  
  check(stockResponse, { 'mixed stock status is 200': (r) => r.status === 200 });
  check(reportsResponse, { 'mixed reports status is 200': (r) => r.status === 200 });
  check(productResponse, { 'mixed product status is 200': (r) => r.status === 200 });
  check(dashboardResponse, { 'mixed dashboard status is 200': (r) => r.status === 200 });
  
  if (stockResponse.status !== 200 || reportsResponse.status !== 200 || 
      productResponse.status !== 200 || dashboardResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Hook de fin de test
export function handleSummary(data) {
  return {
    'results/stress_test_results.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
} 