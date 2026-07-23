"""
extract.py — Extrae de TAB_CONSOLIDADO (Bronze, en Oracle) los registros de
UN indicador, y devuelve un DataFrame con el JSON ya parseado a diccionario
Python (columna 'json'), listo para que cada transform_*.py lo aplane.

IMPORTANTE: la consulta siempre lleva ORDER BY ID ASC. Sin esto, Oracle no
garantiza el orden de las filas devueltas, y como drop_duplicates_report()
usa keep="last" para quedarse con "el registro más reciente" al eliminar
duplicados, sin un orden fijo "el último" cambiaría de forma aleatoria en
cada corrida -- eso causó el bug donde ENEMDU_POBLACIONES daba números
distintos en 2 ejecuciones seguidas. Con ORDER BY ID ASC, "el último" es
siempre el de mayor ID (el insertado más recientemente por el RPA), de
forma consistente y repetible.
"""
import json
import pandas as pd
from db import get_connection


def _parsear_json(datos_json):
    if hasattr(datos_json, "read"):
        raw = datos_json.read()
    else:
        raw = datos_json
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        parsed = json.loads(raw)
        if isinstance(parsed, str):  # algunos indicadores vienen con doble-encode
            parsed = json.loads(parsed)
    else:
        parsed = raw
    return parsed


def extraer_indicador(indicador: str) -> pd.DataFrame:
    """Trae TODAS las filas de un INDICADOR desde TAB_CONSOLIDADO, ordenadas
    por ID para que el resultado sea siempre reproducible.

    Devuelve columnas: id, fecha_extraccion, dato_clave, json (dict ya parseado)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ID, FECHA_EXTRACCION, DATO_CLAVE, DATOS_JSON
            FROM TAB_CONSOLIDADO
            WHERE INDICADOR = :indicador
            ORDER BY ID ASC
            """,
            indicador=indicador,
        )
        rows = []
        for id_, fecha_extraccion, dato_clave, datos_json in cur:
            rows.append({
                "id": id_,
                "fecha_extraccion": fecha_extraccion,
                "dato_clave": dato_clave,
                "json": _parsear_json(datos_json),
            })
        return pd.DataFrame(rows)
    finally:
        conn.close()


def extraer_indicador_chunks(indicador: str, chunk_size: int = 50000):
    """Generador: trae un INDICADOR por lotes en vez de cargar todo en
    memoria de golpe. Útil para SUPERCIAS_RANKING (1.67M filas) si en algún
    momento tu equipo se queda sin RAM con extraer_indicador() normal.

    Uso:
        for chunk_df in extraer_indicador_chunks("SUPERCIAS_RANKING"):
            ...procesar chunk_df...
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.arraysize = chunk_size
        cur.execute(
            """
            SELECT ID, FECHA_EXTRACCION, DATO_CLAVE, DATOS_JSON
            FROM TAB_CONSOLIDADO
            WHERE INDICADOR = :indicador
            ORDER BY ID ASC
            """,
            indicador=indicador,
        )
        total = 0
        while True:
            rows_raw = cur.fetchmany(chunk_size)
            if not rows_raw:
                break
            rows = [
                {
                    "id": id_,
                    "fecha_extraccion": fecha_extraccion,
                    "dato_clave": dato_clave,
                    "json": _parsear_json(datos_json),
                }
                for id_, fecha_extraccion, dato_clave, datos_json in rows_raw
            ]
            total += len(rows)
            print(f"[{indicador}] {total} filas leídas de Oracle...")
            yield pd.DataFrame(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    df = extraer_indicador("PRECIO_PETROLEO_WTI")
    print(df.shape)
    print(df.head())
