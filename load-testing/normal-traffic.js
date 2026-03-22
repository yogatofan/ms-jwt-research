// load-testing/normal-traffic.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Custom metrics
const loginLatency    = new Trend('login_latency',   true);
const productLatency  = new Trend('product_latency', true);
const orderLatency    = new Trend('order_latency',   true);
const errorRate       = new Rate('error_rate');
const totalRequests   = new Counter('total_requests');

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // ramp up ke 10 user
    { duration: '60s', target: 10 },  // tahan 10 user selama 1 menit
    { duration: '30s', target: 0  },  // ramp down
  ],
  thresholds: {
    login_latency:   ['p(95)<500'],   // 95% login < 500ms
    product_latency: ['p(95)<300'],   // 95% get products < 300ms
    order_latency:   ['p(95)<400'],   // 95% post order < 400ms
    error_rate:      ['rate<0.05'],   // error rate < 5%
  },
};

const BASE_URL = 'http://localhost:3000';

export default function () {
  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username: 'user1', password: 'pass123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  loginLatency.add(loginRes.timings.duration);
  totalRequests.add(1);

  const loginOK = check(loginRes, {
    'login status 200': (r) => r.status === 200,
    'token exists':     (r) => r.json('token') !== undefined,
  });
  errorRate.add(!loginOK);

  if (!loginOK) {
    sleep(1); // ← tambahkan sleep di sini sebelum return
    return;
  }

  const token = loginRes.json('token');
  const headers = {
    'Content-Type':  'application/json',
    'Authorization': `Bearer ${token}`,
  };

  sleep(1);

  // Get products
  const productRes = http.get(`${BASE_URL}/products`, { headers });
  productLatency.add(productRes.timings.duration);
  totalRequests.add(1);

  const productOK = check(productRes, {
    'products status 200': (r) => r.status === 200,
    'products not empty':  (r) => {
      const body = r.json();
      return body && body.products && body.products.length > 0;
    },
  });
  errorRate.add(!productOK);

  sleep(1);

  // Create order
  const orderRes = http.post(
    `${BASE_URL}/orders`,
    JSON.stringify({ productId: 1, quantity: 1 }),
    { headers }
  );

  orderLatency.add(orderRes.timings.duration);
  totalRequests.add(1);

  const orderOK = check(orderRes, {
    'order status 201': (r) => r.status === 201,
    'order has id':     (r) => {
      const body = r.json();
      return body && body.order && body.order.id !== undefined;
    },
  });
  errorRate.add(!orderOK);

  sleep(1);
}
