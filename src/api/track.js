const express = require('express');
const router = express.Router();

router.post('/', (req, res) => {
  const event = req.body.event || 'unknown';
  const path = req.body.path || req.path;
  console.log(`TRACK ${req.ip} ${event} ${path}`);
  res.json({ ok: true });
});

module.exports = router;
