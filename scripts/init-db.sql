-- ============================================================
-- INIT BASE DE DONNÉES — Script d'initialisation PostgreSQL
-- Exécuté automatiquement au premier démarrage du container
-- ============================================================

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- Génération UUID
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- Recherche textuelle floue
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- Recherche sans accents

-- Paramètres de performance pour le développement
ALTER SYSTEM SET log_min_duration_statement = '200';  -- Log les requêtes > 200ms
ALTER SYSTEM SET log_statement = 'none';

SELECT pg_reload_conf();
