# Pipeline Macroentorno UTPL — 4to ciclo (SQLite)

Proyecto PyCharm para el Reto "Pipeline de datos del macroentorno ecuatoriano",
alcance **4to ciclo**: Bloque 1 (BCE) + MINEDUC, base de datos SQLite, sin
integración RPA (eso corresponde a la semana 5 en adelante / fuera de este
entregable).

## Nota de consistencia del modelo (actualización)

`fact\\\_indicadores\\\_diarios` y `fact\\\_iee` ahora tienen `id\\\_tiempo` como FK real
hacia `dim\\\_tiempo` (además de conservar su columna `fecha` como llave única
de negocio). Antes solo guardaban `fecha` sin referenciar la dimensión, lo
que dejaba esas dos tablas "sueltas" en el diagrama ER, sin relación con el
resto del modelo. Ya está corregido en `create\\\_tables.sql`, `load.py` y
`modelo\\\_relacional.drawio`.

## Alcance y decisión de cobertura

El documento asigna a 4to ciclo: *"Bloque 1 (BCE) + MINEDUC. Mínimo siete
tablas Silver"* y *"Implementar las cuatro vistas del script base"*. Dos de
esas cuatro vistas (`gold\\\_empresas\\\_provincia` y `gold\\\_bachilleres\\\_vs\\\_empresas`)
necesitan datos de Supercias, que formalmente es Bloque 3 / 6to ciclo. Por
eso se agregó **una sola tabla adicional**, `fact\\\_empresas` (Supercias —
directorio de compañías, no el ranking financiero completo), únicamente para
poder resolver la pregunta P3 del dashboard, que el propio documento marca
como *"la de mayor relevancia estratégica para la UTPL"*. Esto no compromete
el alcance de 4to ciclo: siguen siendo 8 tablas Silver (por encima del
mínimo de 7) y sigue usando SQLite. `gold\\\_empleo\\\_tendencia` (que depende de
ENEMDU, Bloque 2) **no** se implementó — queda fuera de alcance de 4to
ciclo y se deja documentado como pendiente para 6to ciclo.

## Estructura del proyecto

```
project/
├── bronze/                    # Archivos crudos (copiados tal cual del RPA/descarga manual)
│   ├── PIB.xlsx
│   ├── VAB 2018-2023.xlsx
│   ├── PETROLEO.xlsx
│   ├── RIESGO\\\_PAIS.xlsx
│   ├── IEE.xlsx
│   ├── directorio\\\_companias.xlsx
│   └── mineduc\\\_historico.xlsx
├── transform/
│   ├── common.py              # Funciones de limpieza reutilizables (nulos, duplicados, formatos)
│   ├── bce.py                 # Limpieza de las 5 fuentes del Bloque 1
│   ├── mineduc.py             # Limpieza de MINEDUC
│   └── supercias.py           # Limpieza del directorio de compañías (tabla adicional para P3)
├── sql/
│   ├── create\\\_tables.sql      # DDL de las 8 tablas Silver (SQLite)
│   └── gold\\\_views.sql         # 4 vistas Gold que responden P1, P2 (parcial) y P3
├── load.py                    # Orquesta todo el pipeline Bronze -> Silver -> Gold
├── silver\\\_csv/                # Salida intermedia en CSV de cada tabla limpia (se genera al ejecutar)
├── db/
│   └── macroentorno.db        # Base de datos SQLite generada (ábrela con DB Browser for SQLite)
├── modelo\\\_relacional.drawio   # Diagrama ER — importar en draw.io / diagrams.net
└── README.md
```

## Reglas de limpieza aplicadas (las tres que pide el reto)

1. **Tratamiento de nulos**

   * `variacion\\\_pib\\\_pct` nulo en el año 2000 (primer año de la serie PIB): es
correcto y **no se elimina** — no existe año base anterior para calcular
variación (tal como indica el documento). Se documenta con la etiqueta
"Sin dato base" en `gold\\\_pib\\\_tendencia`.
   * `pib\\\_percapita\\\_nominal` nulo en 2025 (previsión): el Excel fuente no
trae ese dato para el año de previsión — se deja nulo, no se inventa un
valor.
   * Filas sin `provincia`/`ruc`/`fecha` (imprescindibles como llave) se
descartan con `dropna`.
   * `total\\\_estudiantes` / `bachilleres\\\_3ero` nulos en MINEDUC se tratan
como 0 (institución sin registro en esa categoría), no como dato
faltante.
2. **Eliminación de duplicados** — `drop\\\_duplicates\\\_report()` en cada fuente,
con reporte impreso de cuántas filas se quitaron (ver log de `load.py`).
Ejemplo real: Supercias tenía 12 RUC duplicados.
3. **Corrección de formatos**

   * Fechas: todas se normalizan a `AAAA-MM-DD` con `pd.to\\\_datetime()` /
`.dt.strftime('%Y-%m-%d')`.
   * Números: `to\\\_numeric\\\_safe()` limpia símbolos y castea a numérico con
coerción (`errors='coerce'`).
   * Texto: `clean\\\_text()` quita espacios extra, colapsa espacios internos y
normaliza a mayúsculas (provincia, cantón, nombre, situación legal).
   * **Bug real detectado y corregido durante la limpieza**: la nota al pie
del Excel de PIB (`"\\\*(p) provisional... previsión... 2025"`) contenía el
número 2025 y el `extract\\\_year()` inicial la confundía con el año 2025
real, sobrescribiendo esa fila. Se corrigió filtrando primero por un
patrón de año válido (`^\\\\d{4}`) antes de extraer el año — un buen
ejemplo de por qué siempre hay que revisar los datos limpios, no
asumir que "ya quedó bien".

## Vistas Gold y qué pregunta responden

|Vista|Pregunta|Qué calcula|
|-|-|-|
|`gold\\\_pib\\\_tendencia`|P1|PIB real anual + variación + clasificación de ciclo económico|
|`gold\\\_petroleo\\\_30dias`|P1 (contexto)|Promedio móvil de 30 días del precio WTI|
|`gold\\\_empresas\\\_provincia`|P2/P3|Empresas activas y totales por provincia|
|`gold\\\_bachilleres\\\_vs\\\_empresas`|**P3**|Bachilleres de 3ero vs. empresas activas por provincia, con ratio|



