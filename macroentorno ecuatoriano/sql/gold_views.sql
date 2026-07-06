-- ============================================================
-- gold_views.sql — Capa Gold (SQLite)
-- Resuelve las 3 preguntas analíticas del dashboard (P1, P2 adaptada, P3)
-- SQLite no soporta "CREATE OR REPLACE VIEW": se usa DROP + CREATE.
-- ============================================================

-- --------------------------------------------------------------
-- 1) gold_pib_tendencia
--    Responde P1: evolución del PIB real + clasificación de ciclo económico
-- --------------------------------------------------------------
DROP VIEW IF EXISTS gold_pib_tendencia;
CREATE VIEW gold_pib_tendencia AS
SELECT
    t.anio,
    m.pib_real_musd,
    m.pib_percapita_nominal,
    m.variacion_pib_pct,
    CASE
        WHEN m.variacion_pib_pct > 2 THEN 'Crecimiento fuerte'
        WHEN m.variacion_pib_pct > 0 THEN 'Crecimiento moderado'
        WHEN m.variacion_pib_pct = 0 THEN 'Estancamiento'
        WHEN m.variacion_pib_pct IS NULL THEN 'Sin dato base (primer año de la serie)'
        ELSE 'Contracción'
    END AS clasificacion
FROM fact_macro_anual m
JOIN dim_tiempo t USING (id_tiempo)
ORDER BY t.anio;

-- --------------------------------------------------------------
-- 2) gold_petroleo_30dias
--    Contexto de coyuntura para P1: promedio móvil de 30 días del WTI
-- --------------------------------------------------------------
DROP VIEW IF EXISTS gold_petroleo_30dias;
CREATE VIEW gold_petroleo_30dias AS
SELECT
    fecha,
    precio_petroleo_wti,
    riesgo_pais_pb,
    ROUND(
        AVG(precio_petroleo_wti) OVER (
            ORDER BY fecha ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    ) AS precio_promedio_30d
FROM fact_indicadores_diarios
ORDER BY fecha;

-- --------------------------------------------------------------
-- 3) gold_empresas_provincia
--    Responde parte de P2/P3: empresas activas por provincia
-- --------------------------------------------------------------
DROP VIEW IF EXISTS gold_empresas_provincia;
CREATE VIEW gold_empresas_provincia AS
SELECT
    g.provincia,
    COUNT(*) AS total_empresas,
    SUM(CASE WHEN e.situacion_legal = 'ACTIVA' THEN 1 ELSE 0 END) AS empresas_activas
FROM fact_empresas e
JOIN dim_geografia g USING (id_geo)
GROUP BY g.provincia
ORDER BY empresas_activas DESC;

-- --------------------------------------------------------------
-- 4) gold_bachilleres_vs_empresas
--    Responde P3: bachilleres de 3ero vs. empresas activas por provincia
--    (la de mayor relevancia estratégica para la UTPL)
-- --------------------------------------------------------------
DROP VIEW IF EXISTS gold_bachilleres_vs_empresas;
CREATE VIEW gold_bachilleres_vs_empresas AS
SELECT
    b.provincia,
    b.bachilleres_3ero,
    COALESCE(emp.empresas_activas, 0) AS empresas_activas,
    ROUND(
        CAST(b.bachilleres_3ero AS REAL) / NULLIF(emp.empresas_activas, 0), 2
    ) AS ratio_bachilleres_por_empresa
FROM (
    SELECT g.provincia, SUM(m.bachilleres_3ero) AS bachilleres_3ero
    FROM fact_mineduc m
    JOIN dim_geografia g USING (id_geo)
    GROUP BY g.provincia
) b
LEFT JOIN gold_empresas_provincia emp ON emp.provincia = b.provincia
ORDER BY ratio_bachilleres_por_empresa DESC;
