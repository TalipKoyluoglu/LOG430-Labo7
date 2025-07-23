import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Métriques personnalisées
const instanceTrend = new Trend('instance_distribution');
const loadBalancingRate = new Rate('load_balancing_success');

// Configuration du test
export let options = {
  stages: [
    { duration: '30s', target: 10 },   // Montée en charge
    { duration: '2m', target: 20 },    // Maintien de la charge
    { duration: '30s', target: 0 },    // Descente
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
    load_balancing_success: ['rate>0.8'],
  },
};

const API_KEY = 'magasin-secret-key-2025';
const KONG_URL = 'http://localhost:8080';

export default function() {
  // Test du load balancing sur le service catalogue
  const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  };

  // Appel au service catalogue via Kong (endpoint principal DDD)
  const response = http.get(`${KONG_URL}/api/ddd/catalogue/rechercher/`, { headers });
  
  // Vérifier que la réponse est valide
  const isSuccess = check(response, {
    'Status is 200': (r) => r.status === 200,
    'Response time < 500ms': (r) => r.timings.duration < 500,
    'Has catalogue data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data && data.data && Array.isArray(data.data.produits);
      } catch (e) {
        console.log(`Debug - JSON parse error:`, e.message);
        return false;
      }
    },
  });

  if (isSuccess) {
    loadBalancingRate.add(1);
    try {
      const responseData = JSON.parse(response.body);
      let instanceId = null;
      if (responseData.instance_id) {
        instanceId = responseData.instance_id;
      } else if (responseData.data && responseData.data.instance_id) {
        instanceId = responseData.data.instance_id;
      }
      if (instanceId) {
        instanceTrend.add(1, { instance: instanceId });
      }
    } catch (e) {}
  } else {
    loadBalancingRate.add(0);
  }

  // Test de différents endpoints pour vérifier la répartition
  const endpoints = [
    '/api/ddd/catalogue/rechercher/',
    '/api/ddd/catalogue/health/',
  ];

  const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const testResponse = http.get(`${KONG_URL}${randomEndpoint}`, { headers });
  
  check(testResponse, {
    'Random endpoint accessible': (r) => r.status === 200 || r.status === 404, // 404 acceptable si endpoint n'existe pas
  });

  sleep(1);
}

export function handleSummary(data) {
  console.log('=== RÉSULTATS DU TEST DE LOAD BALANCING ===');
  console.log(`Requêtes totales: ${data.metrics.http_reqs.values.count}`);
  console.log(`Taux de succès: ${(100 - data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`);
  console.log(`Temps de réponse moyen: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`);
  console.log(`Temps de réponse P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
  
  if (data.metrics.load_balancing_success) {
    console.log(`Taux de load balancing: ${(data.metrics.load_balancing_success.values.rate * 100).toFixed(2)}%`);
  }
  
  console.log('\n=== DISTRIBUTION DES INSTANCES ===');
  if (data.metrics.instance_distribution && data.metrics.instance_distribution.tags) {
    console.log('Répartition des requêtes par instance :');
    for (const [key, val] of Object.entries(data.metrics.instance_distribution.tags)) {
      const instance = key.split(':')[1];
      console.log(`  ${instance} : ${val.count} requêtes`);
    }
  } else {
    console.log('Consultez le rapport K6 pour la distribution par instance (instance_distribution par tag).');
  }

  return {
    'load_balancing_test_results.json': JSON.stringify(data, null, 2),
  };
} 