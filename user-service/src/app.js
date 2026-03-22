require('dotenv').config()
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
app.use(express.json());

const SECRET = process.env.JWT_SECRET || 'research-secret-key';

// Data in-memory (untuk penelitian)
const users = [
  { id: 1, username: 'user1', password: 'pass123' }
];

// Tambahkan di semua service (sebelum routes)
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(JSON.stringify({
      ts: new Date().toISOString(),
      method: req.method,
      path: req.path,
      status: res.statusCode,
      latency_ms: duration
    }));
  });
  next();
});

// POST /auth/login → generate JWT
app.post('/auth/login', (req, res) => {
  const { username, password } = req.body;
  const user = users.find(u => 
    u.username === username && u.password === password
  );
  if (!user) return res.status(401).json({ error: 'Unauthorized' });

  const token = jwt.sign(
    { id: user.id, username: user.username },
    SECRET,
    { expiresIn: '1h' }
  );
  res.json({ token });
});

app.listen(3001, () => console.log('User service: port 3001'));