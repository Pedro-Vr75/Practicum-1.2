"""
transform/supercias.py — Limpieza del Directorio de Compañías (Supercias)

Nota de alcance (4to ciclo): el documento asigna Supercias al Bloque 3 /
6to ciclo, pero la pregunta P3 del dashboard ("bachilleres vs. empresas por
provincia") y las vistas Gold gold_empresas_provincia y
gold_bachilleres_vs_empresas del script base requieren un conteo de empresas
activas por provincia. Por eso se incluye esta única tabla adicional
(fact_empresas) más allá del mínimo de 7 tablas Silver exigido a 4to ciclo,
usando solo las columnas necesarias para el conteo (no el ranking financiero
completo del Bloque 3, que sí queda fuera de alcance).

Fuente de entrada: bronze/directorio_companias.xlsx
  Encabezado real en la fila 5 (index 4) del Excel: No. FILA, EXPEDIENTE, RUC,
  NOMBRE, SITUACIÓN LEGAL, ..., PROVINCIA, CANTÓN, ..., CIIU NIVEL 1, ...
"""
import pandas as pd
from transform.common import clean_text, drop_duplicates_report, report_nulls

COLUMNAS_ORIGEN = ["RUC", "NOMBRE", "SITUACIÓN LEGAL", "PROVINCIA", "CANTÓN", "CIIU NIVEL 1"]


def limpiar_directorio_companias(path: str = "bronze/directorio_companias.xlsx") -> pd.DataFrame:
    df = pd.read_excel(path, header=4, usecols=COLUMNAS_ORIGEN)
    df = df.rename(columns={
        "RUC": "ruc",
        "NOMBRE": "nombre",
        "SITUACIÓN LEGAL": "situacion_legal",
        "PROVINCIA": "provincia",
        "CANTÓN": "canton",
        "CIIU NIVEL 1": "ciiu",
    })

    df["ruc"] = df["ruc"].astype(str).str.strip()
    df["nombre"] = clean_text(df["nombre"])
    df["situacion_legal"] = clean_text(df["situacion_legal"])
    df["provincia"] = clean_text(df["provincia"])
    df["canton"] = clean_text(df["canton"])
    df["ciiu"] = clean_text(df["ciiu"])

    df = df.dropna(subset=["ruc", "provincia"])
    df = df[df["ruc"].str.len() > 5]  # descarta filas basura / totales de pie de página

    df = drop_duplicates_report(df, subset=["ruc"], name="Supercias-directorio")
    report_nulls(df, "Supercias-directorio")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = limpiar_directorio_companias()
    print(df.head())
    print(df["situacion_legal"].value_counts())
