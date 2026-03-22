const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET || 'research-secret-key';

const verifyToken = (req, res, next) => {
  if (process.env.SECURITY_ENABLED !== 'true') return next();

  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) return res.status(401).json({ error: 'Token required' });

  jwt.verify(token, SECRET, (err, decoded) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = decoded;
    next();
  });
};

module.exports = { verifyToken };