require('dotenv').config()
const express = require('express');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// ── Rate Limiters ────────────────────────────────────────────
// Limiter global: semua route (default: 2000 req/menit)
const globalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_GLOBAL_MAX || '2000', 10),
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please slow down.' }
});

// Limiter khusus login (anti brute-force, default: 1000 req/menit)
const authLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_AUTH_MAX || '1000', 10),
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many login attempts, try again later.' }
});

// Terapkan global limiter ke semua route
// SECURITY_ENABLED mengontrol apakah rate limiter aktif
if (process.env.SECURITY_ENABLED === 'true') {
  app.use(globalLimiter);
}

// ── Proxy Routes ─────────────────────────────────────────────
// /auth → user-service (port 3001)
app.use(
  '/auth',
  process.env.SECURITY_ENABLED === 'true' ? authLimiter : (req, res, next) => next(),
  createProxyMiddleware({
    target: 'http://localhost:3001',
    changeOrigin: true,
  })
);

// /products → product-service (port 3002)
app.use(
  '/products',
  createProxyMiddleware({
    target: 'http://localhost:3002',
    changeOrigin: true,
  })
);

// /orders → order-service (port 3003)
app.use(
  '/orders',
  createProxyMiddleware({
    target: 'http://localhost:3003',
    changeOrigin: true,
  })
);

// ── Fallback ─────────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(3000, () => console.log('Gateway: port 3000'));
