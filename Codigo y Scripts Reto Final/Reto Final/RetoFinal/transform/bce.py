"""
transform/bce.py — Aplana y limpia los indicadores del Bloque 1 (BCE)
que llegan como JSON crudo desde TAB_CONSOLIDADO.
"""
import pandas as pd
from extract import extraer_indicador
from transform.common import to_numeric_safe, to_date_iso, clean_text, drop_duplicates_report, report_nulls


def limpiar_pib_real() -> pd.DataFrame:
    df = extraer_indicador("PIB_REAL_PER_CAPITA")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio": to_numeric_safe(j["anio_fiscal"]).astype("Int64"),
        "pib_real_millones": to_numeric_safe(j["pib_real_millones"]),
        "poblacion_total": to_numeric_safe(j["poblacion_total"]),
        "pib_pc_real_usd": to_numeric_safe(j["pib_pc_real_usd"]),
        "tasa_variacion_anual": to_numeric_safe(j["tasa_variacion_anual"]),
    })
    out = drop_duplicates_report(out, subset=["anio"], name="PIB_REAL")
    report_nulls(out, "PIB_REAL")  # tasa_variacion_anual nula en el primer año: esperado, no se elimina
    return out.sort_values("anio").reset_index(drop=True)


def limpiar_pib_nominal() -> pd.DataFrame:
    df = extraer_indicador("PIB_NOMINAL_PER_CAPITA")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio": to_numeric_safe(j["anio_fiscal"]).astype("Int64"),
        "pib_nominal_millones": to_numeric_safe(j["pib_nominal_millones"]),
        "poblacion_total": to_numeric_safe(j["poblacion_total"]),
        "pib_pc_nominal_usd": to_numeric_safe(j["pib_pc_nominal_usd"]),
        "tasa_variacion_anual": to_numeric_safe(j["tasa_variacion_anual"]),
    })
    out = drop_duplicates_report(out, subset=["anio"], name="PIB_NOMINAL")
    report_nulls(out, "PIB_NOMINAL")
    return out.sort_values("anio").reset_index(drop=True)


def _limpiar_serie_diaria(indicador: str, value_name: str) -> pd.DataFrame:
    df = extraer_indicador(indicador)
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "fecha": to_date_iso(j["fecha_fiscal"]),
        value_name: to_numeric_safe(j["valor"]),
    })
    out = out.dropna(subset=["fecha"])
    out = drop_duplicates_report(out, subset=["fecha"], name=indicador)
    report_nulls(out, indicador)
    return out.sort_values("fecha").reset_index(drop=True)


def limpiar_petroleo() -> pd.DataFrame:
    return _limpiar_serie_diaria("PRECIO_PETROLEO_WTI", "precio_petroleo_wti")


def limpiar_riesgo_pais() -> pd.DataFrame:
    return _limpiar_serie_diaria("RIESGO_PAIS", "riesgo_pais_pb")


def limpiar_indicadores_diarios() -> pd.DataFrame:
    petro = limpiar_petroleo()
    riesgo = limpiar_riesgo_pais()
    out = pd.merge(petro, riesgo, on="fecha", how="outer").sort_values("fecha")
    return out.reset_index(drop=True)


def limpiar_iee() -> pd.DataFrame:
    df = extraer_indicador("BCE_IEE_GLOBAL")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "fecha": to_date_iso(j["fecha_publicacion"]),
        "iee_global": to_numeric_safe(j["metricas.iee_global"]),
        "comercio": to_numeric_safe(j["metricas.comercio"]),
        "construccion": to_numeric_safe(j["metricas.construccion"]),
        "manufactura": to_numeric_safe(j["metricas.manufactura"]),
        "servicios": to_numeric_safe(j["metricas.servicios"]),
    })
    out = out.dropna(subset=["fecha"])
    out = drop_duplicates_report(out, subset=["fecha"], name="BCE_IEE_GLOBAL")
    report_nulls(out, "BCE_IEE_GLOBAL")
    return out.sort_values("fecha").reset_index(drop=True)


def limpiar_vab_cantonal() -> pd.DataFrame:
    df = extraer_indicador("VAB_CANTONAL_CIIU")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio": to_numeric_safe(j["anio"]).astype("Int64"),  # nulo real en algunas filas: se conserva
        "codigo_provincia": j["codigo_provincia"],
        "provincia": clean_text(j["provincia"]),
        "codigo_canton": j["codigo_canton"],
        "canton": clean_text(j["canton"]),
        "economia_total": to_numeric_safe(j["sectores.economia_total"]),
    })
    out = drop_duplicates_report(out, subset=["codigo_canton", "anio"], name="VAB_CANTONAL")
    report_nulls(out, "VAB_CANTONAL")
    return out.reset_index(drop=True)


def _limpiar_matriz_empleo(indicador: str, value_name: str) -> pd.DataFrame:
    df = extraer_indicador(indicador)
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio": to_numeric_safe(j["anio"]).astype("Int64"),
        "codigo_cie": j["codigo_cie"],
        "seccion": clean_text(j["seccion"]),
        "industria": clean_text(j["industria"]),
        value_name: to_numeric_safe(j["valor"]),
    })
    out = drop_duplicates_report(out, subset=["anio", "industria"], name=indicador)
    report_nulls(out, indicador)
    return out.reset_index(drop=True)


def limpiar_matriz_empleo_total() -> pd.DataFrame:
    return _limpiar_matriz_empleo("MATRIZ_EMPLEO_TOTAL", "num_personas")


def limpiar_matriz_empleo_vab() -> pd.DataFrame:
    return _limpiar_matriz_empleo("MATRIZ_EMPLEO_VAB", "vab_miles_usd")


if __name__ == "__main__":
    print(limpiar_pib_real().tail())
    print(limpiar_indicadores_diarios().tail())
    print(limpiar_iee().tail())
