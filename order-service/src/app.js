require('dotenv').config()
const express = require('express');
const app = express();
app.use(express.json());

const { verifyToken } = require('./middleware/auth');

// Data in-memory
const orders = [];
let nextOrderId = 1;

// Logging latency
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    console.log(JSON.stringify({
      ts: new Date().toISOString(),
      service: 'order-service',
      method: req.method,
      path: req.path,
      status: res.statusCode,
      latency_ms: Date.now() - start
    }));
  });
  next();
});

// GET /orders → ambil semua order milik user (butuh token)
app.get('/orders', verifyToken, (req, res) => {
  const userOrders = orders.filter(o => o.userId === req.user.id);
  res.json({ orders: userOrders });
});

// POST /orders → buat order baru (butuh token)
app.post('/orders', verifyToken, (req, res) => {
  const { productId, quantity } = req.body;

  if (!productId || !quantity) {
    return res.status(400).json({ error: 'productId and quantity are required' });
  }

  const order = {
    id: nextOrderId++,
    userId: req.user.id,
    productId,
    quantity,
    createdAt: new Date().toISOString()
  };

  orders.push(order);
  res.status(201).json({ order });
});

app.listen(3003, () => console.log('Order service: port 3003'));