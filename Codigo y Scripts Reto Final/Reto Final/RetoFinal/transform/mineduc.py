"""
transform/mineduc.py — Aplana y limpia MINEDUC_AMIE_COSTA desde TAB_CONSOLIDADO.
"""
import pandas as pd
from extract import extraer_indicador
from transform.common import to_numeric_safe, clean_text, drop_duplicates_report, report_nulls


def limpiar_mineduc() -> pd.DataFrame:
    df = extraer_indicador("MINEDUC_AMIE_COSTA")
    j = pd.json_normalize(df["json"])

    out = pd.DataFrame({
        "periodo_lectivo": j["periodo_lectivo"].astype(str).str.strip(),
        "anio_base": to_numeric_safe(j["anio_base"]).astype("Int64"),
        "amie": j["institucion.amie"].astype(str).str.strip(),
        "nombre_institucion": clean_text(j["institucion.nombre"]),
        "provincia": clean_text(j["institucion.provincia"]),
        "canton": clean_text(j["institucion.canton"]),
        "sostenimiento": clean_text(j["institucion.sostenimiento"]),
        "total_estudiantes": to_numeric_safe(j["estudiantes_resumen.total_estudiantes"]).fillna(0),
        "bach_3ero_m": to_numeric_safe(j["estudiantes_detallado.bachillerato_3er_ano.m"]).fillna(0),
        "bach_3ero_h": to_numeric_safe(j["estudiantes_detallado.bachillerato_3er_ano.h"]).fillna(0),
    })
    out["bachilleres_3ero"] = out["bach_3ero_m"] + out["bach_3ero_h"]
    out = out.drop(columns=["bach_3ero_m", "bach_3ero_h"])

    out = drop_duplicates_report(out, subset=["amie", "periodo_lectivo"], name="MINEDUC")
    report_nulls(out, "MINEDUC")
    return out.reset_index(drop=True)


if __name__ == "__main__":
    df = limpiar_mineduc()
    print(df.shape)
    print(df.head())
