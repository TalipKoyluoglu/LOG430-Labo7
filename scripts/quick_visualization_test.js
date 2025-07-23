import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Montée à 5 utilisateurs
    { duration: '1m', target: 5 },    // Maintenir 5 utilisateurs
    { duration: '30s', target: 10 },  // Montée à 10 utilisateurs
    { duration: '1m', target: 10 },   // Maintenir 10 utilisateurs
    { duration: '30s', target: 0 },   // Redescendre à 0
  ],
};

export default function () {
  const group = __VU % 3;
  
  switch (group) {
    case 0:
      // Test des rapports
      const reportsResponse = http.get('http://localhost:8000/api/v1/reports/');
      check(reportsResponse, { 'reports status is 200': (r) => r.status === 200 });
      break;
    case 1:
      // Test du stock
      const stockResponse = http.get('http://localhost:8000/api/v1/stores/1/stock/');
      check(stockResponse, { 'stock status is 200': (r) => r.status === 200 });
      break;
    case 2:
      // Test des produits
      const productResponse = http.get('http://localhost:8000/api/v1/products/1/');
      check(productResponse, { 'product status is 200': (r) => r.status === 200 });
      break;
  }
  
  sleep(1);
} 