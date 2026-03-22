// load-testing/run-experiment.js
// Jalankan ini untuk kedua kondisi, output otomatis tersimpan ke file

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const latency   = new Trend('response_latency', true);
const errorRate = new Rate('error_rate');

export const options = {
  scenarios: {
    normal_load: {
      executor: 'constant-vus',
      vus: 20,
      duration: '60s',
    },
  },
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const BASE_URL = 'http://localhost:3000';

export default function () {
  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username: 'user1', password: 'pass123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  latency.add(loginRes.timings.duration);
  const ok = check(loginRes, { 'status 200': (r) => r.status === 200 });
  errorRate.add(!ok);

  if (!ok) return;

  const token = loginRes.json('token');
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  const productRes = http.get(`${BASE_URL}/products`, { headers });
  latency.add(productRes.timings.duration);
  errorRate.add(productRes.status !== 200);

  sleep(1);
}
