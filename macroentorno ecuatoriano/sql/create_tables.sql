-- ============================================================
-- create_tables.sql — Capa Silver (SQLite, 4to ciclo)
-- Proyecto: Pipeline Macroentorno UTPL — Bloque 1 (BCE) + MINEDUC
-- Motor: SQLite (DB Browser for SQLite)
-- ============================================================
PRAGMA foreign_keys = ON;

-- Dimensión geográfica (compartida entre VAB, MINEDUC y Supercias)
DROP TABLE IF EXISTS dim_geografia;
CREATE TABLE dim_geografia (
    id_geo        INTEGER PRIMARY KEY AUTOINCREMENT,
    provincia     VARCHAR(60) NOT NULL,
    cod_provincia INTEGER,
    canton        VARCHAR(80),
    cod_canton    INTEGER,
    UNIQUE(provincia, canton)
);

-- Dimensión temporal
DROP TABLE IF EXISTS dim_tiempo;
CREATE TABLE dim_tiempo (
    id_tiempo INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha     DATE NOT NULL UNIQUE,
    anio      INTEGER NOT NULL,
    mes       INTEGER,
    trimestre INTEGER
);

-- Hechos: indicadores macroeconómicos anuales (PIB real, per cápita, variación)
DROP TABLE IF EXISTS fact_macro_anual;
CREATE TABLE fact_macro_anual (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tiempo             INTEGER REFERENCES dim_tiempo(id_tiempo),
    pib_real_musd         NUMERIC(14,2),
    pib_percapita_nominal NUMERIC(10,2),
    variacion_pib_pct     NUMERIC(6,3)
);

-- Hechos: indicadores diarios (petróleo WTI + riesgo país)
DROP TABLE IF EXISTS fact_indicadores_diarios;
CREATE TABLE fact_indicadores_diarios (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tiempo           INTEGER REFERENCES dim_tiempo(id_tiempo),
    fecha               DATE NOT NULL UNIQUE,
    precio_petroleo_wti NUMERIC(8,2),
    riesgo_pais_pb      INTEGER
);

-- Hechos: Índice de Expectativas Empresariales (mensual)
DROP TABLE IF EXISTS fact_iee;
CREATE TABLE fact_iee (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tiempo     INTEGER REFERENCES dim_tiempo(id_tiempo),
    fecha         DATE NOT NULL UNIQUE,
    iee_global    NUMERIC(6,2),
    comercio      NUMERIC(6,2),
    construccion  NUMERIC(6,2),
    manufactura   NUMERIC(6,2),
    servicios     NUMERIC(6,2)
);

-- Hechos: VAB por provincia/cantón/sector
DROP TABLE IF EXISTS fact_vab;
CREATE TABLE fact_vab (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_geo         INTEGER REFERENCES dim_geografia(id_geo),
    anio           INTEGER NOT NULL,
    sector         VARCHAR(120),
    vab_miles_usd  NUMERIC(16,2)
);

-- Hechos: MINEDUC — estudiantes y bachilleres 3ero por provincia/cantón
DROP TABLE IF EXISTS fact_mineduc;
CREATE TABLE fact_mineduc (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    id_geo            INTEGER REFERENCES dim_geografia(id_geo),
    periodo           VARCHAR(20) NOT NULL,
    anio              INTEGER,
    sostenimiento     VARCHAR(40),
    total_estudiantes INTEGER,
    bachilleres_3ero  INTEGER
);

-- Hechos: Supercias — empresas por provincia (tabla adicional, ver transform/supercias.py)
DROP TABLE IF EXISTS fact_empresas;
CREATE TABLE fact_empresas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_geo          INTEGER REFERENCES dim_geografia(id_geo),
    ruc             VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(200),
    situacion_legal VARCHAR(40),
    ciiu            VARCHAR(150)
);

-- Índices de apoyo para las vistas Gold
CREATE INDEX IF NOT EXISTS idx_fact_vab_geo   ON fact_vab(id_geo);
CREATE INDEX IF NOT EXISTS idx_fact_mineduc_geo ON fact_mineduc(id_geo);
CREATE INDEX IF NOT EXISTS idx_fact_empresas_geo ON fact_empresas(id_geo);
