"""
Funciones comunes de limpieza reutilizadas por todos los módulos transform/*.py

Reglas de limpieza aplicadas en todo el pipeline (Bronze -> Silver):
  1. Tratamiento de nulos      -> dropna_if_key(), fillna explícito documentado por columna
  2. Eliminación de duplicados -> drop_duplicates_report()
  3. Corrección de formatos    -> to_numeric_safe(), to_date_iso(), clean_text()
"""
import unicodedata
import pandas as pd


def clean_text(serie: pd.Series) -> pd.Series:
    """Quita espacios extra, colapsa espacios internos y pasa a mayúsculas.
    Usado en columnas categóricas de texto (provincia, cantón, nombre, etc.)."""
    s = serie.astype(str).str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    s = s.str.upper()
    s = s.replace({"NAN": None, "NONE": None, "": None})
    return s


def strip_accents(serie: pd.Series) -> pd.Series:
    """Normaliza acentos (útil para hacer join de provincias con distinta ortografía)."""
    def _strip(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return x
        return "".join(
            c for c in unicodedata.normalize("NFKD", str(x)) if not unicodedata.combining(c)
        )
    return serie.map(_strip)


def to_numeric_safe(serie: pd.Series) -> pd.Series:
    """Convierte a numérico forzando coerción; strings tipo '1.234,56' o con
    espacios / símbolos se limpian antes de castear."""
    cleaned = (
        serie.astype(str)
        .str.replace(r"[^\d,.\-]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def to_date_iso(serie: pd.Series, dayfirst: bool = False) -> pd.Series:
    """Convierte una columna de fechas (string, datetime o Timestamp de Excel)
    al formato ISO AAAA-MM-DD, devolviendo un pandas datetime64 (para poder
    seguir operando) — al exportar se formatea con .dt.strftime('%Y-%m-%d')."""
    return pd.to_datetime(serie, errors="coerce", dayfirst=dayfirst)


def extract_year(serie: pd.Series) -> pd.Series:
    """Extrae los primeros 4 dígitos de una celda tipo '2024 (prel)' o '2025(Prev)'."""
    return serie.astype(str).str.extract(r"(\d{4})")[0].astype("Int64")


def drop_duplicates_report(df: pd.DataFrame, subset=None, name: str = "") -> pd.DataFrame:
    """Elimina duplicados e imprime cuántas filas se quitaron (para el log de decisiones)."""
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="last")
    after = len(df)
    if before != after:
        print(f"[{name}] Duplicados eliminados: {before - after} (quedan {after} filas)")
    return df


def marcar_encoding_irrecuperable(serie: pd.Series):
    """El carácter U+FFFD ('�') significa que un byte no se pudo decodificar
    y el dato original YA SE PERDIÓ de forma irreversible en el origen (RPA/
    scraping), no en este pipeline. No se puede "adivinar" qué letra era, así
    que NO se reemplaza por una letra inventada.

    Esta función solo estandariza el símbolo para que sea fácil de detectar y
    reportar (ej. contar cuántas filas están afectadas), y deja constancia en
    el propio dato de que ese registro tiene una limitación conocida de la
    fuente -- en vez de dejarlo silenciosamente como si el dato estuviera
    íntegro.

    Devuelve una tupla (serie_original, serie_booleana_de_filas_dañadas).
    """
    tiene_dano = serie.astype(str).str.contains("\ufffd", na=False)
    if tiene_dano.any():
        print(f"  [AVISO] {tiene_dano.sum()} valores con caracteres irrecuperables "
              f"(encoding dañado en el origen/RPA, no en este pipeline).")
    return serie, tiene_dano


def report_nulls(df: pd.DataFrame, name: str = "") -> None:
    """Imprime resumen de nulos por columna, para documentar decisiones de limpieza."""
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        print(f"[{name}] Nulos por columna:\n{nulls.to_string()}")
    else:
        print(f"[{name}] Sin nulos remanentes.")
