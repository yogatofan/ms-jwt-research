require('dotenv').config()
const express = require('express');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// ── Rate Limiters ────────────────────────────────────────────
// Limiter global: semua route
const globalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,  // ← naikkan dari 100 ke 10000 untuk testing
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please slow down.' }
});

// Limiter ketat khusus login (anti brute-force)
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,  // ← naikkan dari 10 ke 10000 untuk testing
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
