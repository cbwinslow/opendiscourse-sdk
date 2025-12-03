const express = require('express');
const router = express.Router();

router.post('/login', (req, res) => {
  const { username } = req.body;
  if (!username) return res.status(400).json({ error: 'username required' });
  req.session.user = username;
  res.json({ success: true });
});

router.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.json({ success: true });
  });
});

router.get('/whoami', (req, res) => {
  res.json({ user: req.session.user || null });
});

module.exports = router;
