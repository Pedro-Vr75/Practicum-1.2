"""
transform/mineduc.py — Limpieza de la fuente MINEDUC (Bloque 3, requerida en 4to ciclo)

Fuente de entrada: bronze/mineduc_historico.xlsx
  Registro administrativo histórico AMIE (2009-2023), a nivel de institución educativa.

El documento describe una versión simplificada (AMIE 2023-2024) con columnas
Ao_lectivo, AMIE, Nombre_Institucion, Provincia, Canton, Nivel_Educacion,
Sostenimiento, Total_Estudiantes. El archivo real entregado es el histórico
completo (104 columnas por institución), así que se adapta la limpieza:
  - Se toma el período más reciente disponible (2022-2023 Inicio).
  - La columna '3er Año Bachillerato' ya viene desagregada por año de
    bachillerato, por lo que representa directamente a los "bachilleres
    próximos a graduarse" que pide la pregunta P3 (no hace falta filtrar
    Nivel_Educacion + último grado como en la versión simplificada).
  - Se agrega (sum) a nivel provincia/cantón/sostenimiento para no cargar
    290k filas innecesarias en Silver.
"""
import pandas as pd
from transform.common import clean_text, to_numeric_safe, drop_duplicates_report, report_nulls

ULTIMO_PERIODO = "2022-2023 Inicio"

COLUMNAS_ORIGEN = [
    "Periodo", "Provincia", "Canton", "Tipo_Educacion", "Sostenimiento",
    "Total_Estudiantes", "3er Año Bachillerato",
]


def limpiar_mineduc(path: str = "bronze/mineduc_historico.xlsx",
                     periodo: str = ULTIMO_PERIODO) -> pd.DataFrame:
    df = pd.read_excel(path, usecols=COLUMNAS_ORIGEN)
    df = df.rename(columns={
        "Periodo": "periodo",
        "Provincia": "provincia",
        "Canton": "canton",
        "Tipo_Educacion": "tipo_educacion",
        "Sostenimiento": "sostenimiento",
        "Total_Estudiantes": "total_estudiantes",
        "3er Año Bachillerato": "bachilleres_3ero",
    })

    df["provincia"] = clean_text(df["provincia"])
    df["canton"] = clean_text(df["canton"])
    df["tipo_educacion"] = clean_text(df["tipo_educacion"])
    df["sostenimiento"] = clean_text(df["sostenimiento"])
    df["total_estudiantes"] = to_numeric_safe(df["total_estudiantes"]).fillna(0)
    df["bachilleres_3ero"] = to_numeric_safe(df["bachilleres_3ero"]).fillna(0)

    df = df.dropna(subset=["provincia", "periodo"])

    # Filtra al período más reciente para evitar duplicar series históricas en Silver
    df = df[df["periodo"] == periodo]

    # Agregado por provincia/cantón/sostenimiento (reduce ~290k filas a un tamaño manejable)
    agg = (
        df.groupby(["periodo", "provincia", "canton", "sostenimiento"], dropna=False)
        .agg(total_estudiantes=("total_estudiantes", "sum"),
             bachilleres_3ero=("bachilleres_3ero", "sum"))
        .reset_index()
    )
    agg["anio"] = agg["periodo"].str.extract(r"(\d{4})").astype("Int64")

    agg = drop_duplicates_report(agg, subset=["periodo", "provincia", "canton", "sostenimiento"],
                                  name="MINEDUC")
    report_nulls(agg, "MINEDUC")
    return agg.reset_index(drop=True)


if __name__ == "__main__":
    print(limpiar_mineduc().head(15))
