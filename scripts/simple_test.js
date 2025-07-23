import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,
  duration: '10s',
};

export default function () {
  const response = http.get('http://localhost:8000/api/v1/reports/');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
} 