const express = require('express');
const router = express.Router();

router.post('/', async (req, res) => {
  const { question } = req.body;
  // Placeholder: integrate LangChain or other RAG pipeline
  res.json({ answer: `You asked: ${question}` });
});

module.exports = router;
