"""
transform/bce.py — Limpieza de las 5 fuentes del Bloque 1 (Banco Central del Ecuador)

Fuentes de entrada (bronze/):
  - PIB.xlsx                 -> PIB real anual + PIB per cápita nominal + variación
  - VAB 2018-2023.xlsx        -> VAB por provincia/cantón/sector
  - PETROLEO.xlsx             -> precio petróleo WTI diario
  - RIESGO_PAIS.xlsx          -> riesgo país diario
  - IEE.xlsx                  -> Índice de Expectativas Empresariales mensual

Cada función retorna un DataFrame ya limpio, listo para cargar a Silver.
"""
import pandas as pd
from transform.common import (
    to_numeric_safe, to_date_iso, extract_year, clean_text,
    drop_duplicates_report, report_nulls,
)


def limpiar_pib(path: str = "bronze/PIB.xlsx") -> pd.DataFrame:
    """PIB real anual (millones USD), PIB per cápita nominal y variación %.

    Decisiones de limpieza:
      - Se descartan filas de pie de página (notas, asteriscos) que no tienen año válido.
      - AÑO viene con sufijos como '2024 (prel)' o '2025(Prev)' -> se extraen solo los 4 dígitos.
      - La variación del primer año (2000) es nula por diseño: NO se elimina, se documenta
        (no hay año anterior con el que calcular variación).
    """
    df = pd.read_excel(path, sheet_name="Hoja1")
    df = df.rename(columns={
        "AÑO": "anio_raw",
        "PIB 2018 = 100.1": "pib_real_musd",
        "VAR ANUAL PIB": "variacion_pib_pct",
        "PIB PER CÁPITA NOMINAL": "pib_percapita_nominal",
    })
    # Las notas al pie del Excel (ej. "*(p) provisional ... previsión ... 2025")
    # también contienen 4 dígitos y serían mal interpretadas como año, así que
    # primero se descartan filas cuyo campo AÑO no empieza con un año (patrón
    # 'AAAA' u 'AAAA (texto)'), y solo luego se extraen los 4 dígitos.
    patron_anio_valido = df["anio_raw"].astype(str).str.match(r"^\d{4}")
    df = df[patron_anio_valido]
    df["anio"] = extract_year(df["anio_raw"])
    df = df.dropna(subset=["anio"])  # quita notas al pie / filas sin año

    for col in ["pib_real_musd", "variacion_pib_pct", "pib_percapita_nominal"]:
        df[col] = to_numeric_safe(df[col])
    df["variacion_pib_pct"] = (df["variacion_pib_pct"] * 100).round(3)

    df = df[["anio", "pib_real_musd", "pib_percapita_nominal", "variacion_pib_pct"]]
    df = drop_duplicates_report(df, subset=["anio"], name="PIB")
    report_nulls(df, "PIB")
    # Nulo esperado y válido: variacion_pib_pct del primer año (no hay año base anterior)
    return df.reset_index(drop=True)


def limpiar_vab(path: str = "bronze/VAB 2018-2023.xlsx") -> pd.DataFrame:
    """VAB por provincia/cantón/sector (2018-2023)."""
    df = pd.read_excel(path, sheet_name="DATA")
    df = df.rename(columns={
        "AÑO": "anio",
        "CÓDIGO PROVINCIA": "cod_provincia",
        "PROVINCIA": "provincia",
        "CÓDIGO CANTÓN": "cod_canton",
        "CANTÓN": "canton",
        "SECTOR": "sector",
        "VALOR": "vab_miles_usd",
    })
    df["provincia"] = clean_text(df["provincia"])
    df["canton"] = clean_text(df["canton"])
    df["sector"] = clean_text(df["sector"])
    df["anio"] = to_numeric_safe(df["anio"]).astype("Int64")
    df["cod_provincia"] = to_numeric_safe(df["cod_provincia"]).astype("Int64")
    df["cod_canton"] = to_numeric_safe(df["cod_canton"]).astype("Int64")
    df["vab_miles_usd"] = to_numeric_safe(df["vab_miles_usd"])

    df = df.dropna(subset=["provincia", "anio", "vab_miles_usd"])
    df = drop_duplicates_report(
        df, subset=["anio", "cod_canton", "sector"], name="VAB"
    )
    report_nulls(df, "VAB")
    return df.reset_index(drop=True)


def _limpiar_serie_diaria(path: str, value_name: str) -> pd.DataFrame:
    """Función genérica para PETROLEO.xlsx y RIESGO_PAIS.xlsx: mismo formato
    (col 0 = 'Período' + fila de encabezado duplicada en la fila 0 de datos)."""
    df = pd.read_excel(path, sheet_name="Ark1", header=1)
    df.columns = ["fecha", value_name]
    df["fecha"] = to_date_iso(df["fecha"])
    df[value_name] = to_numeric_safe(df[value_name])
    df = df.dropna(subset=["fecha"])
    df = drop_duplicates_report(df, subset=["fecha"], name=value_name)
    report_nulls(df, value_name)
    return df.sort_values("fecha").reset_index(drop=True)


def limpiar_petroleo(path: str = "bronze/PETROLEO.xlsx") -> pd.DataFrame:
    """Precio diario del petróleo WTI en USD/barril."""
    return _limpiar_serie_diaria(path, "precio_petroleo_wti")


def limpiar_riesgo_pais(path: str = "bronze/RIESGO_PAIS.xlsx") -> pd.DataFrame:
    """Riesgo país diario en puntos básicos."""
    return _limpiar_serie_diaria(path, "riesgo_pais_pb")


def limpiar_indicadores_diarios() -> pd.DataFrame:
    """Combina petróleo + riesgo país en una sola tabla fact_indicadores_diarios,
    tal como sugiere el documento ('pueden estar en el mismo archivo o separados')."""
    petro = limpiar_petroleo()
    riesgo = limpiar_riesgo_pais()
    df = pd.merge(petro, riesgo, on="fecha", how="outer").sort_values("fecha")
    return df.reset_index(drop=True)


def limpiar_iee(path: str = "bronze/IEE.xlsx") -> pd.DataFrame:
    """Índice de Expectativas Empresariales mensual (desde 2010)."""
    df = pd.read_excel(path, sheet_name="IEE", header=7)
    df = df.rename(columns={
        "Fecha": "fecha",
        "IEE Global (2)": "iee_global",
        "Comercio": "comercio",
        "Construcción": "construccion",
        "Manufactura": "manufactura",
        "Servicios": "servicios",
    })
    df["fecha"] = to_date_iso(df["fecha"])
    for col in ["iee_global", "comercio", "construccion", "manufactura", "servicios"]:
        df[col] = to_numeric_safe(df[col])
    df = df.dropna(subset=["fecha"])
    df = drop_duplicates_report(df, subset=["fecha"], name="IEE")
    report_nulls(df, "IEE")
    return df.sort_values("fecha").reset_index(drop=True)


if __name__ == "__main__":
    print(limpiar_pib().head())
    print(limpiar_vab().head())
    print(limpiar_indicadores_diarios().head())
    print(limpiar_iee().head())
