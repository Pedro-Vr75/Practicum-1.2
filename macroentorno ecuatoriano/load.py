"""
load.py — Orquesta el pipeline completo Bronze -> Silver -> Gold para SQLite.

Uso (desde PyCharm o terminal, parado en la raíz del proyecto):
    python load.py

Genera:
    db/macroentorno.db   -> base de datos SQLite lista para abrir en DB Browser for SQLite
    silver_csv/*.csv      -> copia de cada tabla limpia, por si se quiere inspeccionar aparte
"""
import sqlite3
from pathlib import Path

import pandas as pd

from transform.bce import limpiar_pib, limpiar_vab, limpiar_indicadores_diarios, limpiar_iee
from transform.mineduc import limpiar_mineduc
from transform.supercias import limpiar_directorio_companias

DB_PATH = Path("db/macroentorno.db")
SQL_DIR = Path("sql")
CSV_DIR = Path("silver_csv")


def build_dim_geografia(conn, *dfs_con_geo):
    """Construye dim_geografia a partir de todas las combinaciones únicas
    provincia/cantón que aparezcan en VAB, MINEDUC y Supercias."""
    frames = []
    for df, prov_col, cant_col, codp_col, codc_col in dfs_con_geo:
        cols = {"provincia": df[prov_col]}
        cols["canton"] = df[cant_col] if cant_col else None
        cols["cod_provincia"] = df[codp_col] if codp_col else None
        cols["cod_canton"] = df[codc_col] if codc_col else None
        frames.append(pd.DataFrame(cols))
    geo = pd.concat(frames, ignore_index=True)
    geo = geo.dropna(subset=["provincia"]).drop_duplicates(subset=["provincia", "canton"])
    geo.to_sql("dim_geografia", conn, if_exists="append", index=False)

    lookup = pd.read_sql("SELECT id_geo, provincia, canton FROM dim_geografia", conn)
    return lookup


def attach_geo_id(df, lookup, prov_col, cant_col):
    tmp = df.copy()
    tmp = tmp.merge(
        lookup, left_on=[prov_col, cant_col], right_on=["provincia", "canton"], how="left"
    )
    return tmp


def build_dim_tiempo(conn, fechas: pd.Series):
    fechas = pd.to_datetime(pd.Series(fechas).dropna().unique())
    dim = pd.DataFrame({"fecha": fechas})
    dim["anio"] = dim["fecha"].dt.year
    dim["mes"] = dim["fecha"].dt.month
    dim["trimestre"] = dim["fecha"].dt.quarter
    dim["fecha"] = dim["fecha"].dt.strftime("%Y-%m-%d")
    dim = dim.drop_duplicates(subset=["fecha"]).sort_values("fecha")
    dim.to_sql("dim_tiempo", conn, if_exists="append", index=False)
    return pd.read_sql("SELECT id_tiempo, fecha FROM dim_tiempo", conn)


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SQL_DIR.joinpath("create_tables.sql").read_text(encoding="utf-8"))

    print("== Limpiando fuentes BCE ==")
    pib = limpiar_pib()
    vab = limpiar_vab()
    diarios = limpiar_indicadores_diarios()
    iee = limpiar_iee()

    print("== Limpiando MINEDUC ==")
    mineduc = limpiar_mineduc()

    print("== Limpiando Supercias (tabla adicional para P3) ==")
    empresas = limpiar_directorio_companias()

    for name, df in [("pib", pib), ("vab", vab), ("indicadores_diarios", diarios),
                      ("iee", iee), ("mineduc", mineduc), ("empresas", empresas)]:
        df.to_csv(CSV_DIR / f"{name}.csv", index=False)

    # --- dim_geografia (VAB + MINEDUC + Supercias) ---
    lookup = build_dim_geografia(
        conn,
        (vab, "provincia", "canton", "cod_provincia", "cod_canton"),
        (mineduc, "provincia", "canton", None, None),
        (empresas, "provincia", "canton", None, None),
    )

    vab_geo = attach_geo_id(vab, lookup, "provincia", "canton")
    vab_geo[["id_geo", "anio", "sector", "vab_miles_usd"]].to_sql(
        "fact_vab", conn, if_exists="append", index=False
    )

    mineduc_geo = attach_geo_id(mineduc, lookup, "provincia", "canton")
    mineduc_geo[["id_geo", "periodo", "anio", "sostenimiento",
                 "total_estudiantes", "bachilleres_3ero"]].to_sql(
        "fact_mineduc", conn, if_exists="append", index=False
    )

    empresas_geo = attach_geo_id(empresas, lookup, "provincia", "canton")
    empresas_geo[["id_geo", "ruc", "nombre", "situacion_legal", "ciiu"]].to_sql(
        "fact_empresas", conn, if_exists="append", index=False
    )

    # --- dim_tiempo (PIB anual + serie diaria + IEE mensual) ---
    fechas_pib = pd.to_datetime(pib["anio"].astype(str) + "-01-01")
    todas_fechas = pd.concat([fechas_pib, diarios["fecha"], iee["fecha"]])
    tiempo_lookup = build_dim_tiempo(conn, todas_fechas)

    pib_t = pib.copy()
    pib_t["fecha"] = pd.to_datetime(pib_t["anio"].astype(str) + "-01-01").dt.strftime("%Y-%m-%d")
    pib_t = pib_t.merge(tiempo_lookup, on="fecha", how="left")
    pib_t[["id_tiempo", "pib_real_musd", "pib_percapita_nominal", "variacion_pib_pct"]].to_sql(
        "fact_macro_anual", conn, if_exists="append", index=False
    )

    diarios_out = diarios.copy()
    diarios_out["fecha"] = diarios_out["fecha"].dt.strftime("%Y-%m-%d")
    diarios_out = diarios_out.merge(tiempo_lookup, on="fecha", how="left")
    diarios_out[["id_tiempo", "fecha", "precio_petroleo_wti", "riesgo_pais_pb"]].to_sql(
        "fact_indicadores_diarios", conn, if_exists="append", index=False
    )

    iee_out = iee.copy()
    iee_out["fecha"] = iee_out["fecha"].dt.strftime("%Y-%m-%d")
    iee_out = iee_out.merge(tiempo_lookup, on="fecha", how="left")
    iee_out[["id_tiempo", "fecha", "iee_global", "comercio", "construccion", "manufactura", "servicios"]].to_sql(
        "fact_iee", conn, if_exists="append", index=False
    )

    # --- Vistas Gold ---
    conn.executescript(SQL_DIR.joinpath("gold_views.sql").read_text(encoding="utf-8"))
    conn.commit()

    print("\n== Verificación de vistas Gold ==")
    for view in ["gold_pib_tendencia", "gold_petroleo_30dias",
                 "gold_empresas_provincia", "gold_bachilleres_vs_empresas"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {view}: {n} filas")

    conn.close()
    print(f"\nBase de datos generada en: {DB_PATH.resolve()}")
    print("Ábrela con DB Browser for SQLite para explorar tablas Silver y vistas Gold.")


if __name__ == "__main__":
    main()
