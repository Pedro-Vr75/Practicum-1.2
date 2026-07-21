-- ============================================================
-- gold_views_sqlite.sql — Capa Gold (SQLite)
-- SQLite no soporta "CREATE OR REPLACE VIEW": se usa DROP + CREATE.
-- ============================================================

-- 1) P1: PIB real anual + clasificación del ciclo económico
DROP VIEW IF EXISTS GOLD_PIB_TENDENCIA;
CREATE VIEW GOLD_PIB_TENDENCIA AS
SELECT
    r.anio,
    r.pib_real_millones,
    n.pib_pc_nominal_usd,
    r.tasa_variacion_anual,
    CASE
        WHEN r.tasa_variacion_anual > 2 THEN 'Crecimiento fuerte'
        WHEN r.tasa_variacion_anual > 0 THEN 'Crecimiento moderado'
        WHEN r.tasa_variacion_anual = 0 THEN 'Estancamiento'
        WHEN r.tasa_variacion_anual IS NULL THEN 'Sin dato base (primer anio de la serie)'
        ELSE 'Contraccion'
    END AS clasificacion
FROM SILVER_PIB_REAL r
LEFT JOIN SILVER_PIB_NOMINAL n ON n.anio = r.anio
ORDER BY r.anio;

-- 2) Contexto de P1: petróleo + riesgo país, promedio móvil 30 días
DROP VIEW IF EXISTS GOLD_PETROLEO_30DIAS;
CREATE VIEW GOLD_PETROLEO_30DIAS AS
SELECT
    fecha,
    precio_petroleo_wti,
    riesgo_pais_pb,
    ROUND(
        AVG(precio_petroleo_wti) OVER (
            ORDER BY fecha ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    ) AS precio_promedio_30d
FROM SILVER_INDICADORES_DIARIOS
ORDER BY fecha;

-- 3) P2/P3: empresas activas por provincia
DROP VIEW IF EXISTS GOLD_EMPRESAS_PROVINCIA;
CREATE VIEW GOLD_EMPRESAS_PROVINCIA AS
SELECT
    provincia,
    COUNT(*) AS total_empresas,
    SUM(CASE WHEN situacion_legal = 'ACTIVA' THEN 1 ELSE 0 END) AS empresas_activas
FROM SILVER_SUPERCIAS_DIRECTORIO
GROUP BY provincia
ORDER BY empresas_activas DESC;

-- 4) P3: bachilleres 3ero vs. empresas activas por provincia
DROP VIEW IF EXISTS GOLD_BACHILLERES_VS_EMPRESAS;
CREATE VIEW GOLD_BACHILLERES_VS_EMPRESAS AS
SELECT
    b.provincia,
    b.bachilleres_3ero,
    COALESCE(emp.empresas_activas, 0) AS empresas_activas,
    ROUND(
        CAST(b.bachilleres_3ero AS REAL) / NULLIF(emp.empresas_activas, 0), 2
    ) AS ratio_bachilleres_por_empresa
FROM (
    SELECT provincia, SUM(bachilleres_3ero) AS bachilleres_3ero
    FROM SILVER_MINEDUC
    GROUP BY provincia
) b
LEFT JOIN GOLD_EMPRESAS_PROVINCIA emp ON emp.provincia = b.provincia
ORDER BY ratio_bachilleres_por_empresa DESC;

-- 5) Nueva: tendencia de población urbana/rural (ENEMDU)
DROP VIEW IF EXISTS GOLD_EMPLEO_TENDENCIA;
CREATE VIEW GOLD_EMPLEO_TENDENCIA AS
SELECT
    anio_fiscal,
    mes_fiscal,
    nacional_total,
    area_urbana,
    area_rural,
    ROUND(CAST(area_urbana AS REAL) / NULLIF(nacional_total,0) * 100, 2) AS pct_urbano
FROM SILVER_ENEMDU_POBLACIONES
ORDER BY anio_fiscal, mes_fiscal;

-- 6) Nueva: empleo total por sección CIIU y año (Matriz de Empleo BCE)
DROP VIEW IF EXISTS GOLD_EMPLEO_POR_SECTOR;
CREATE VIEW GOLD_EMPLEO_POR_SECTOR AS
SELECT
    anio,
    seccion,
    SUM(num_personas) AS total_empleados
FROM SILVER_MATRIZ_EMPLEO_TOTAL
GROUP BY anio, seccion
ORDER BY anio DESC, total_empleados DESC;

-- 7) Nueva: VAB por provincia y año (agregado desde el detalle cantonal)
DROP VIEW IF EXISTS GOLD_VAB_PROVINCIA;
CREATE VIEW GOLD_VAB_PROVINCIA AS
SELECT
    anio,
    provincia,
    SUM(economia_total) AS vab_total
FROM SILVER_VAB_CANTONAL
WHERE anio IS NOT NULL
GROUP BY anio, provincia
ORDER BY anio DESC, vab_total DESC;
