import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

// Métriques personnalisées
const errorRate = new Rate('errors');

// Configuration du test
export const options = {
  stages: [
    // Phase de montée en charge progressive
    { duration: '2m', target: 10 },  // 0 à 10 utilisateurs en 2 minutes
    { duration: '5m', target: 10 },  // Maintenir 10 utilisateurs pendant 5 minutes
    { duration: '2m', target: 20 },  // Augmenter à 20 utilisateurs
    { duration: '5m', target: 20 },  // Maintenir 20 utilisateurs
    { duration: '2m', target: 0 },   // Redescendre à 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% des requêtes < 2s
    http_req_failed: ['rate<0.1'],     // Taux d'erreur < 10%
    errors: ['rate<0.1'],              // Taux d'erreur personnalisé < 10%
  },
};

// Configuration de base
const BASE_URL = 'http://localhost';
const AUTH_TOKEN = 'token-430';

// Headers communs
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Token ${AUTH_TOKEN}`,
};

// Fonction principale du test
export default function () {
  const group = __VU % 3; // Répartir les utilisateurs virtuels en 3 groupes

  switch (group) {
    case 0:
      // Groupe 1: Consultation des stocks de plusieurs magasins
      testStockConsultation();
      break;
    case 1:
      // Groupe 2: Génération de rapports consolidés
      testReportsGeneration();
      break;
    case 2:
      // Groupe 3: Mise à jour de produits à forte fréquence
      testProductUpdates();
      break;
  }

  sleep(1); // Pause entre les requêtes
}

// Test 1: Consultation des stocks
function testStockConsultation() {
  const storeIds = [1, 2, 3]; // IDs de magasins à tester
  const storeId = storeIds[__VU % storeIds.length];
  
  // Test endpoint stock simple
  const stockResponse = http.get(`${BASE_URL}/api/v1/stores/${storeId}/stock/`);
  check(stockResponse, {
    'stock consultation status is 200': (r) => r.status === 200,
    'stock consultation response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  // Test endpoint stock avec pagination et filtrage
  const stockListResponse = http.get(
    `${BASE_URL}/api/v1/stores/${storeId}/stock/list/?page=1&ordering=-quantite`
  );
  check(stockListResponse, {
    'stock list status is 200': (r) => r.status === 200,
    'stock list has pagination': (r) => JSON.parse(r.body).hasOwnProperty('results'),
  });
  
  if (stockResponse.status !== 200 || stockListResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Test 2: Génération de rapports
function testReportsGeneration() {
  // Test rapport des ventes
  const reportsResponse = http.get(`${BASE_URL}/api/v1/reports/`);
  check(reportsResponse, {
    'reports status is 200': (r) => r.status === 200,
    'reports response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  // Test dashboard performances
  const dashboardResponse = http.get(`${BASE_URL}/api/v1/dashboard/`);
  check(dashboardResponse, {
    'dashboard status is 200': (r) => r.status === 200,
    'dashboard has performance data': (r) => r.body.length > 0,
  });
  
  if (reportsResponse.status !== 200 || dashboardResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Test 3: Mise à jour de produits
function testProductUpdates() {
  const productIds = [1, 2, 3, 4, 5]; // IDs de produits à mettre à jour
  const productId = productIds[__VU % productIds.length];
  
  // Données de mise à jour
  const updateData = {
    nom: `Produit mis à jour - VU${__VU}`,
    prix: 15.99 + (__VU * 0.1), // Prix légèrement différent par VU
    description: `Description mise à jour par VU ${__VU}`,
  };
  
  const updateResponse = http.put(
    `${BASE_URL}/api/v1/products/${productId}/`,
    JSON.stringify(updateData),
    { headers }
  );
  
  check(updateResponse, {
    'product update status is 200': (r) => r.status === 200,
    'product update response time < 1500ms': (r) => r.timings.duration < 1500,
  });
  
  if (updateResponse.status !== 200) {
    errorRate.add(1);
  }
}

// Hook de fin de test
export function handleSummary(data) {
  return {
    'results/baseline_test_results.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
} 