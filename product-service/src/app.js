require('dotenv').config()
const express = require('express');
const app = express();
app.use(express.json());

const { verifyToken } = require('./middleware/auth');

// Data in-memory
const products = [
  { id: 1, name: 'Laptop',  price: 15000000 },
  { id: 2, name: 'Mouse',   price: 250000  },
  { id: 3, name: 'Keyboard', price: 500000 },
];

// Logging latency
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    console.log(JSON.stringify({
      ts: new Date().toISOString(),
      service: 'product-service',
      method: req.method,
      path: req.path,
      status: res.statusCode,
      latency_ms: Date.now() - start
    }));
  });
  next();
});

// GET /products → ambil semua produk (butuh token)
app.get('/products', verifyToken, (req, res) => {
  res.json({ products });
});

// GET /products/:id → ambil satu produk (butuh token)
app.get('/products/:id', verifyToken, (req, res) => {
  const product = products.find(p => p.id === parseInt(req.params.id));
  if (!product) return res.status(404).json({ error: 'Product not found' });
  res.json({ product });
});

app.listen(3002, () => console.log('Product service: port 3002'));