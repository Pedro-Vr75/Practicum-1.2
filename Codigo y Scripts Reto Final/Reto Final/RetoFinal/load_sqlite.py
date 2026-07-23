"""
load_sqlite.py — Orquesta el pipeline completo:
  Oracle (TAB_CONSOLIDADO, Bronze/JSON) -> Python (limpieza) -> SQLite (.db)

Genera un archivo SQLite local (db/macroentorno_silver.db) para abrir
directo en DB Browser for SQLite.

Uso (desde PyCharm o terminal, parado en la raíz del proyecto):
    python load_sqlite.py

Requiere:
    pip install oracledb pandas
"""
import sqlite3
from pathlib import Path

import pandas as pd

from transform.bce import (
    limpiar_pib_real, limpiar_pib_nominal, limpiar_indicadores_diarios,
    limpiar_iee, limpiar_vab_cantonal, limpiar_matriz_empleo_total, limpiar_matriz_empleo_vab,
)
from transform.censo import limpiar_censo_ocupacion, limpiar_censo_rama, limpiar_enemdu_poblaciones
from transform.mineduc import limpiar_mineduc
from transform.supercias import limpiar_directorio_companias, limpiar_supercias_ranking

DB_PATH = Path("db/macroentorno_silver.db")


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)

    print("== Bloque 1: BCE ==")
    pib_real = limpiar_pib_real()
    pib_nominal = limpiar_pib_nominal()
    diarios = limpiar_indicadores_diarios()
    iee = limpiar_iee()
    vab = limpiar_vab_cantonal()
    empleo_total = limpiar_matriz_empleo_total()
    empleo_vab = limpiar_matriz_empleo_vab()

    print("== Bloque 2: INEC ==")
    censo_ocup = limpiar_censo_ocupacion()
    censo_rama = limpiar_censo_rama()
    enemdu_pob = limpiar_enemdu_poblaciones()

    print("== Bloque 3: MINEDUC + Supercias ==")
    mineduc = limpiar_mineduc()
    directorio = limpiar_directorio_companias()
    ranking = limpiar_supercias_ranking()

    # --- Escribir cada DataFrame limpio como tabla Silver en SQLite ---
    tablas = {
        "SILVER_PIB_REAL": pib_real,
        "SILVER_PIB_NOMINAL": pib_nominal,
        "SILVER_INDICADORES_DIARIOS": diarios,
        "SILVER_IEE": iee,
        "SILVER_VAB_CANTONAL": vab,
        "SILVER_MATRIZ_EMPLEO_TOTAL": empleo_total,
        "SILVER_MATRIZ_EMPLEO_VAB": empleo_vab,
        "SILVER_CENSO_OCUPACION": censo_ocup,
        "SILVER_CENSO_RAMA": censo_rama,
        "SILVER_ENEMDU_POBLACIONES": enemdu_pob,
        "SILVER_MINEDUC": mineduc,
        "SILVER_SUPERCIAS_DIRECTORIO": directorio,
        "SILVER_SUPERCIAS_RANKING": ranking,
    }

    for nombre, df in tablas.items():
        df_out = df.copy()
        # SQLite no tiene tipo fecha nativo -- se guardan como texto ISO
        for col in df_out.select_dtypes(include=["datetime64[ns]"]).columns:
            df_out[col] = df_out[col].dt.strftime("%Y-%m-%d")
        df_out.to_sql(nombre, conn, if_exists="replace", index=False, chunksize=5000)
        print(f"[{nombre}] {len(df_out)} filas escritas en SQLite.")

    conn.commit()

    # --- Crear las vistas Gold ---
    with open("sql/gold_views_sqlite.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    print("\n== Verificación de vistas Gold ==")
    vistas = [
        "GOLD_PIB_TENDENCIA", "GOLD_PETROLEO_30DIAS", "GOLD_EMPRESAS_PROVINCIA",
        "GOLD_BACHILLERES_VS_EMPRESAS", "GOLD_EMPLEO_TENDENCIA", "GOLD_EMPLEO_POR_SECTOR",
        "GOLD_VAB_PROVINCIA",
    ]
    for v in vistas:
        n = conn.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        print(f"  {v}: {n} filas")

    conn.close()
    print(f"\nBase de datos generada en: {DB_PATH.resolve()}")
    print("Ábrela con DB Browser for SQLite para explorar tablas Silver y vistas Gold.")


if __name__ == "__main__":
    main()
