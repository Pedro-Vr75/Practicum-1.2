"""
transform/censo.py — Aplana y limpia los indicadores del Bloque 2 (INEC:
Censo 2022 + ENEMDU) que llegan como JSON crudo desde TAB_CONSOLIDADO.
"""
import pandas as pd
from extract import extraer_indicador
from transform.common import to_numeric_safe, clean_text, drop_duplicates_report, report_nulls, marcar_encoding_irrecuperable


def limpiar_censo_ocupacion() -> pd.DataFrame:
    df = extraer_indicador("CENSO_GRUPO_OCUPACION")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio_censo": to_numeric_safe(j["anio_censo"]).astype("Int64"),
        "provincia": clean_text(j["provincia"]),
        "canton": clean_text(j["canton"]),
        "sexo": clean_text(j["sexo"]),
        "rango_edad": j["rango_edad"].astype(str).str.strip(),
        "total_ocupados": to_numeric_safe(j["total_ocupados"]).fillna(0),
    })
    # El RPA que extrajo el Censo INEC dañó de forma irreversible algunos
    # caracteres especiales (tildes/ñ) -- se documenta con una columna, no se
    # inventa el texto correcto (confirmado inspeccionando el .sql fuente).
    canton_limpio, danado = marcar_encoding_irrecuperable(out["canton"])
    out["canton"] = canton_limpio
    out["canton_encoding_danado"] = danado.astype(int)  # 0/1, más seguro para Oracle/SQLite
    out = drop_duplicates_report(
        out, subset=["provincia", "canton", "sexo", "rango_edad"], name="CENSO_OCUPACION"
    )
    report_nulls(out, "CENSO_OCUPACION")
    return out.reset_index(drop=True)


def limpiar_censo_rama() -> pd.DataFrame:
    df = extraer_indicador("CENSO_RAMA_ACTIVIDAD")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio_censo": to_numeric_safe(j["anio_censo"]).astype("Int64"),
        "provincia": clean_text(j["provincia"]),
        "canton": clean_text(j["canton"]),
        "sexo": clean_text(j["sexo"]),
        "rango_edad": j["rango_edad"].astype(str).str.strip(),
        "total_ocupados": to_numeric_safe(j["total_ocupados"]).fillna(0),
    })
    canton_limpio, danado = marcar_encoding_irrecuperable(out["canton"])
    out["canton"] = canton_limpio
    out["canton_encoding_danado"] = danado.astype(int)
    out = drop_duplicates_report(
        out, subset=["provincia", "canton", "sexo", "rango_edad"], name="CENSO_RAMA"
    )
    report_nulls(out, "CENSO_RAMA")
    return out.reset_index(drop=True)


def limpiar_enemdu_poblaciones() -> pd.DataFrame:
    df = extraer_indicador("INEC_ENEMDU_POBLACIONES")
    j = pd.json_normalize(df["json"])
    out = pd.DataFrame({
        "anio_fiscal": to_numeric_safe(j["anio_fiscal"]).astype("Int64"),
        "mes_fiscal": to_numeric_safe(j["mes_fiscal"]).astype("Int64"),
        "nacional_total": to_numeric_safe(j["metricas.nacional_total"]),
        "area_urbana": to_numeric_safe(j["metricas.area_urbana"]),
        "area_rural": to_numeric_safe(j["metricas.area_rural"]),
        "sexo_hombre": to_numeric_safe(j["metricas.sexo_hombre"]),
        "sexo_mujer": to_numeric_safe(j["metricas.sexo_mujer"]),
    })
    out = drop_duplicates_report(out, subset=["anio_fiscal", "mes_fiscal"], name="ENEMDU_POBLACIONES")
    report_nulls(out, "ENEMDU_POBLACIONES")
    return out.sort_values(["anio_fiscal", "mes_fiscal"]).reset_index(drop=True)


if __name__ == "__main__":
    print(limpiar_censo_ocupacion().head())
    print(limpiar_enemdu_poblaciones().tail())
