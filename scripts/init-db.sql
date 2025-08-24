-- Initialize database with required extensions

-- Create UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database for testing if not exists
SELECT 'CREATE DATABASE memory_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'memory_test_db')\gexec
