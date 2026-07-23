# Pipeline RPA: Oracle (Bronze) → Python (limpieza) → SQLite (Silver + Gold)

Este proyecto lee los 14 indicadores crudos desde Oracle (`TAB_CONSOLIDADO`),
los limpia con Python/pandas (nulos, duplicados, formatos), y escribe un
archivo **SQLite `.db` local**, listo para abrir en DB Browser for SQLite.

## Flujo

```
Oracle (TAB_CONSOLIDADO, 14 indicadores JSON)
        │  extract.py + transform/*.py  (limpieza: nulos, duplicados, formatos)
        ▼
db/macroentorno_silver.db
        ├── 13 tablas SILVER_*  (datos limpios)
        └── 7 vistas GOLD_*     (listas para Power BI / DB Browser)
```

## Cómo ejecutar

1. Ajusta `db.py` con tu usuario/contraseña/conexión Oracle real
   (por defecto: `admin / pwdadmin / localhost:1521/XEPDB1`).
2. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Ejecuta:
   ```
   python load_sqlite.py
   ```
4. Abre `db/macroentorno_silver.db` con **DB Browser for SQLite**.

## Reglas de limpieza aplicadas (las 3 del reto)

1. **Nulos**: `tasa_variacion_anual` nulo en el primer año de la serie de
   PIB (real y nominal) y `anio` nulo en algunas filas de VAB — nulos reales
   de la fuente, se documentan y NO se eliminan ni se inventan.
2. **Duplicados**: `drop_duplicates_report()` con la llave natural de cada
   indicador (fecha para series diarias, RUC para empresas, expediente+año
   para el ranking, AMIE+periodo para MINEDUC). El orden de extracción usa
   `ORDER BY ID ASC` en `extract.py` para que el resultado sea siempre
   reproducible (antes de este fix, sin el ORDER BY, Oracle no garantizaba
   el orden de las filas y `drop_duplicates(keep="last")` podía tomar un
   registro distinto en cada corrida — esto se detectó y corrigió durante
   las pruebas con `ENEMDU_POBLACIONES`, que daba números distintos en 2
   ejecuciones seguidas antes del fix).
3. **Formatos**: fechas a `AAAA-MM-DD`, números con `to_numeric_safe()`
   (coerción segura), texto con `clean_text()` (trim + mayúsculas).

## Limitación de datos documentada (no oculta)

`SILVER_CENSO_OCUPACION` y `SILVER_CENSO_RAMA` tienen una columna
`canton_encoding_danado` (0/1): marca las filas donde el nombre del cantón
llegó con pérdida irreversible de tildes/ñ (carácter U+FFFD, "�") desde el
RPA original. Se confirmó inspeccionando el archivo `.sql` fuente en texto
plano (antes de tocar Oracle) que el daño ya venía desde el origen del
scraping, no de este pipeline de limpieza — por eso no se intenta
"adivinar" la ortografía correcta, solo se documenta con evidencia.

## Tablas Silver generadas (13)

BCE: `SILVER_PIB_REAL`, `SILVER_PIB_NOMINAL`, `SILVER_INDICADORES_DIARIOS`,
`SILVER_IEE`, `SILVER_VAB_CANTONAL`, `SILVER_MATRIZ_EMPLEO_TOTAL`,
`SILVER_MATRIZ_EMPLEO_VAB`.

INEC: `SILVER_CENSO_OCUPACION`, `SILVER_CENSO_RAMA`, `SILVER_ENEMDU_POBLACIONES`.

MINEDUC + Supercias: `SILVER_MINEDUC`, `SILVER_SUPERCIAS_DIRECTORIO`,
`SILVER_SUPERCIAS_RANKING`.

## Vistas Gold generadas (7)

| Vista | Qué responde |
|---|---|
| `GOLD_PIB_TENDENCIA` | P1 — PIB real y clasificación del ciclo económico |
| `GOLD_PETROLEO_30DIAS` | P1 (contexto) — petróleo y riesgo país |
| `GOLD_EMPRESAS_PROVINCIA` | P2/P3 — empresas activas por provincia |
| `GOLD_BACHILLERES_VS_EMPRESAS` | P3 — bachilleres vs. empresas por provincia |
| `GOLD_EMPLEO_TENDENCIA` | Nueva — población urbana/rural (ENEMDU) |
| `GOLD_EMPLEO_POR_SECTOR` | Nueva — empleo total por sección CIIU y año |
| `GOLD_VAB_PROVINCIA` | Nueva — VAB agregado por provincia y año |

## Rendimiento

`SILVER_SUPERCIAS_RANKING` (1.67M filas) es la tabla más pesada. Si tu
equipo se queda sin memoria durante la extracción, usa
`extraer_indicador_chunks()` (ya incluida en `extract.py`) en vez de
`extraer_indicador()` para ese indicador específico.
