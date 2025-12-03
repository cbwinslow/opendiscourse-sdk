const express = require('express');
const { Pool } = require('pg');
const Joi = require('joi');

const router = express.Router();

// Validate required environment variables
const requiredEnvVars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
}

// Configure database connection pool with error handling
const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT, 10),
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  max: 20, // Maximum number of clients in the pool
  idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
  connectionTimeoutMillis: 2000, // Return error after 2 seconds if connection could not be established
});

// Handle pool errors
pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});


  try {
    // Validate query parameters
    const { error, value } = querySchema.validate(req.query);
    if (error) {
      return res.status(400).json({ 
        error: 'Invalid query parameters', 
        details: error.details.map(detail => detail.message)
      });
    }

    const { limit, offset, search, source_type } = value;
    
    // Build query with proper parameterization
    let query = 'SELECT id, title, source_url, source_type, source_date, created_at FROM documents';
    const params = [];
    const conditions = [];
    
    if (search) {
      conditions.push('title ILIKE $' + (params.length + 1));
      params.push(`%${search}%`);
    }
    
    if (source_type) {
      conditions.push('source_type = $' + (params.length + 1));
      params.push(source_type);
    }
    
    if (conditions.length > 0) {
      query += ' WHERE ' + conditions.join(' AND ');
    }
    
    query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1) + ' OFFSET $' + (params.length + 2);
    params.push(limit, offset);

    // Execute query with timeout
    const client = await pool.connect();
    try {
      const result = await client.query(query, params);
      
      // Get total count for pagination
      let countQuery = 'SELECT COUNT(*) FROM documents';
      const countParams = [];
      
      if (conditions.length > 0) {
        countQuery += ' WHERE ' + conditions.join(' AND ');
        // Use the same search conditions for count
        if (search) countParams.push(`%${search}%`);
        if (source_type) countParams.push(source_type);
      }
      
      const countResult = await client.query(countQuery, countParams);
      const totalCount = parseInt(countResult.rows[0].count, 10);
      
      res.json({
        documents: result.rows,
        pagination: {
          limit,
          offset,
          total: totalCount,
          hasMore: offset + limit < totalCount
        }
      });
    } finally {
      client.release();
    }
    
  } catch (err) {
    console.error('Database query error:', err);
    
    // Return appropriate error response
    if (err.code === 'ECONNREFUSED') {
      res.status(503).json({ error: 'Database connection failed' });
    } else if (err.code === '42P01') {
      res.status(500).json({ error: 'Database table not found' });
    } else {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

module.exports = router;
