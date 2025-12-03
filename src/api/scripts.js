const express = require('express');
const fs = require('fs');
const { execFile } = require('child_process');

const router = express.Router();
const scriptsDir = `${__dirname}/../../scripts`;

router.get('/', (req, res) => {
  fs.readdir(scriptsDir, (err, files) => {
    if (err) return res.status(500).json({ error: err.message });
    const pyFiles = files.filter(f => f.endsWith('.py'));
    res.json(pyFiles);
  });
});

router.post('/run', (req, res) => {
  const { script, args = [] } = req.body;

  });
});

module.exports = router;
