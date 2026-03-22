// load-testing/burst-traffic.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const loginLatency   = new Trend('login_latency',   true);
const productLatency = new Trend('product_latency', true);
const errorRate      = new Rate('error_rate');
const blockedReqs    = new Counter('blocked_requests'); // request yang kena rate limit
const totalRequests  = new Counter('total_requests');

export const options = {
  stages: [
    { duration: '10s', target: 50  },  // spike cepat ke 50 user
    { duration: '30s', target: 200 },  // naik drastis ke 200 user
    { duration: '20s', target: 200 },  // tahan di 200 user
    { duration: '10s', target: 0   },  // drop
  ],
  thresholds: {
    error_rate: ['rate<0.8'], // toleransi tinggi, karena memang attack scenario
  },
};

const BASE_URL = 'http://localhost:3000';

export default function () {
  // Simulasi brute-force login
  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username: 'user1', password: 'pass123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  loginLatency.add(loginRes.timings.duration);
  totalRequests.add(1);

  // Catat request yang kena block rate limiter (status 429)
  if (loginRes.status === 429) {
    blockedReqs.add(1);
  }

  check(loginRes, {
    'login 200': (r) => r.status === 200,
    'rate limited 429': (r) => r.status === 429, // ini justru bagus = rate limit bekerja
  });
  errorRate.add(loginRes.status !== 200 && loginRes.status !== 429);

  if (loginRes.status !== 200) return;

  const token = loginRes.json('token');
  const headers = {
    'Content-Type':  'application/json',
    'Authorization': `Bearer ${token}`,
  };

  // Bombardir endpoint products tanpa sleep
  for (let i = 0; i < 5; i++) {
    const productRes = http.get(`${BASE_URL}/products`, { headers });
    productLatency.add(productRes.timings.duration);
    totalRequests.add(1);

    if (productRes.status === 429) blockedReqs.add(1);
  }

  sleep(0.5);
}