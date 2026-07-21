"""
transform/supercias.py — Aplana y limpia SUPERCIAS_DIRECTORIO y
SUPERCIAS_RANKING desde TAB_CONSOLIDADO.
"""
import pandas as pd
from extract import extraer_indicador
from transform.common import clean_text, to_numeric_safe, drop_duplicates_report, report_nulls


def limpiar_directorio_companias() -> pd.DataFrame:
    df = extraer_indicador("SUPERCIAS_DIRECTORIO")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "ruc": j["empresa_metadata.ruc"].astype(str).str.strip(),
        "nombre": clean_text(j["empresa_metadata.nombre"]),
        "situacion_legal": clean_text(j["empresa_metadata.situacion_legal"]),
        "provincia": clean_text(j["ubicacion.provincia"]),
        "canton": clean_text(j["ubicacion.canton"]),
        "ciiu_nivel1": j["financiero_ciiu.ciiu_nivel1"].astype(str).str.strip(),
    })
    out = out.dropna(subset=["ruc", "provincia"])
    out = out[out["ruc"].str.len() > 5]
    out = drop_duplicates_report(out, subset=["ruc"], name="SUPERCIAS_DIRECTORIO")
    report_nulls(out, "SUPERCIAS_DIRECTORIO")
    return out.reset_index(drop=True)


def limpiar_supercias_ranking() -> pd.DataFrame:
    """Solo trae los campos esenciales del ranking (no los 50 campos financieros
    completos), suficientes para la vista Gold de empresas por provincia/CIIU."""
    df = extraer_indicador("SUPERCIAS_RANKING")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "expediente": to_numeric_safe(j["EXPEDIENTE"]).astype("Int64"),
        "anio": to_numeric_safe(j["ANIO"]).astype("Int64"),
        "ciiu_n1": j["CIIU_N1"].astype(str).str.strip(),
        "n_empleados": to_numeric_safe(j["N_EMPLEADOS"]).fillna(0),
        "ingresos_ventas": to_numeric_safe(j["INGRESOS_VENTAS"]),
        "utilidad_neta": to_numeric_safe(j["UTILIDAD_NETA"]),
        "activos": to_numeric_safe(j["ACTIVOS"]),
    })
    out = drop_duplicates_report(out, subset=["expediente", "anio"], name="SUPERCIAS_RANKING")
    report_nulls(out, "SUPERCIAS_RANKING")
    return out.reset_index(drop=True)


if __name__ == "__main__":
    print(limpiar_directorio_companias().head())
    print(limpiar_supercias_ranking().head())
