"""
=========================================================
 MÓDULO DE INGESTA Y LIMPIEZA - FUENTES BCE
=========================================================
Reto: Limpieza fuentes BCE
Objetivo: Implementar funciones de limpieza para PIB real, PIB nominal,
VAB, petróleo/riesgo país e IEE, y cargar las cinco tablas resultantes
(capa Silver) en la base de datos SQLite del proyecto.

NOTA SOBRE RUTAS (fix del error "No such file or directory"):
---------------------------------------------------------
El error original ocurría porque el script usaba rutas RELATIVAS
('datos_macroentorno/archivo.xlsx'). Una ruta relativa depende de cuál
sea el "directorio de trabajo" (working directory) desde el que se
ejecuta Python, y en PyCharm eso varía según la configuración de
ejecución (Run Configuration) que se use.

La solución: todas las rutas se construyen a partir de la ubicación
del propio archivo bce.py (usando __file__), subiendo un nivel hasta
la raíz del proyecto (RetoS2Final) y entrando a datos_macroentorno/.
Así el script funciona sin importar desde dónde lo ejecutes (botón
Run de PyCharm, terminal, consola interactiva, etc.).
"""

import os
import sqlite3
import sys

import pandas as pd

# =========================================================
# RUTAS BASE DEL PROYECTO (independientes del working directory)
# =========================================================

# Carpeta donde está este archivo: .../RetoS2Final/transform
DIR_TRANSFORM = os.path.dirname(os.path.abspath(__file__))

# Raíz del proyecto: .../RetoS2Final
DIR_RAIZ = os.path.dirname(DIR_TRANSFORM)

# Carpeta de datos crudos (capa Bronze)
DIR_DATOS = os.path.join(DIR_RAIZ, 'datos_macroentorno')

# Base de datos de salida (capa Silver)
BD_PATH = os.path.join(DIR_TRANSFORM, 'pipeline_utpl.db')


# =========================================================
# UTILIDAD: verificación amistosa de archivos de entrada
# =========================================================

def _verificar_archivo(ruta):
    """
    Comprueba que el archivo exista antes de intentar leerlo.
    Lanza un FileNotFoundError con un mensaje claro indicando
    exactamente qué archivo falta y en qué carpeta se esperaba.
    """
    if not os.path.isfile(ruta):
        raise FileNotFoundError(
            f"No se encontró el archivo esperado:\n"
            f"   {ruta}\n"
            f"   Verifica que el archivo exista dentro de la carpeta "
            f"'datos_macroentorno/' del proyecto."
        )
    return ruta


# =========================================================
# MÓDULO DE INGESTA Y LIMPIEZA - FUENTES BCE
# =========================================================

def procesar_pib_constante(ruta_excel):
    """PIB real (constante) per cápita - hoja 'PIB pc real'."""
    print("-> Iniciando limpieza del PIB Real Anual...")
    _verificar_archivo(ruta_excel)

    datos_crudos = pd.read_excel(ruta_excel, sheet_name='PIB pc real', engine='openpyxl')
    fila_titulos = datos_crudos[datos_crudos.iloc[:, 0] == 'Años'].index[0]

    df_pib = pd.read_excel(ruta_excel, sheet_name='PIB pc real', header=fila_titulos + 1, engine='openpyxl')

    # Estandarización de columnas
    df_pib.rename(columns={
        'Años': 'anio',
        'PIB \n(Millones de USD encadenado de volumen)': 'pib_real_musd',
        'Población': 'poblacion_miles',
        'PIB Per cápita  \n(USD)': 'pib_percapita_usd',
        'Tasa de variación anual del PIB Per cápita\n(En porcentaje)': 'variacion_pib_pct'
    }, inplace=True)

    # Limpieza de nulos y casteo del año
    df_pib.dropna(subset=['pib_real_musd'], inplace=True)
    df_pib['anio'] = df_pib['anio'].astype(str).str.replace(' (p)', '', regex=False).astype(int)

    return df_pib


def procesar_pib_corriente(ruta_excel):
    """PIB nominal per cápita - hoja índice 5 ('PIB pc nominal')."""
    print("-> Extrayendo PIB Nominal...")
    _verificar_archivo(ruta_excel)

    # Uso del índice 5 para evitar errores por espacios en el nombre de la hoja
    datos_crudos = pd.read_excel(ruta_excel, sheet_name=5, engine='openpyxl')
    fila_titulos = datos_crudos[datos_crudos.iloc[:, 0] == 'Años'].index[0]

    df_nom = pd.read_excel(ruta_excel, sheet_name=5, header=fila_titulos + 1, engine='openpyxl')
    columnas_orig = df_nom.columns.tolist()

    df_nom.rename(columns={
        columnas_orig[0]: 'periodo',
        columnas_orig[3]: 'pib_percapita_nominal_usd'
    }, inplace=True)

    df_nom.dropna(subset=['pib_percapita_nominal_usd'], inplace=True)
    df_nom['periodo'] = df_nom['periodo'].astype(str).str.replace(' (p)', '', regex=False).astype(int)

    # Filtro post-dolarización y creación de fecha
    df_filtrado = df_nom[df_nom['periodo'] >= 2000].copy()
    df_filtrado['fecha'] = pd.to_datetime(df_filtrado['periodo'], format='%Y')

    return df_filtrado[['fecha', 'periodo', 'pib_percapita_nominal_usd']]


def limpiar_wti_embi(ruta_csv):
    """Petróleo WTI y riesgo país (EMBI) - serie diaria."""
    print("-> Procesando WTI y Riesgo País...")
    _verificar_archivo(ruta_csv)

    df_diario = pd.read_csv(ruta_csv)
    df_diario.rename(columns={'Período': 'fecha'}, inplace=True)
    df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
    return df_diario


def formatear_iee(ruta_csv):
    """Índice de Expectativas Económicas (IEE) - serie mensual."""
    print("-> Normalizando IEE Mensual...")
    _verificar_archivo(ruta_csv)

    df_mensual = pd.read_csv(ruta_csv)
    df_mensual.columns = [c.lower() for c in df_mensual.columns]
    df_mensual['fecha'] = pd.to_datetime(df_mensual['fecha'], format='%Y-%m-%d')
    return df_mensual


def preparar_vab_regional(ruta_csv):
    """Valor Agregado Bruto (VAB) provincial."""
    print("-> Estructurando VAB Provincial...")
    _verificar_archivo(ruta_csv)

    df_prov = pd.read_csv(ruta_csv)
    df_prov.columns = [c.lower() for c in df_prov.columns]
    df_prov.rename(columns={'año': 'anio'}, inplace=True)
    return df_prov


# =========================================================
# CARGA A LA CAPA SILVER
# =========================================================

def guardar_en_sqlite(dataframe, tabla_destino, conx):
    dataframe.to_sql(tabla_destino, conx, if_exists='replace', index=False)
    print(f"   [OK] Tabla '{tabla_destino}' creada con éxito ({len(dataframe)} filas).")


# =========================================================
# FLUJO PRINCIPAL
# =========================================================

if __name__ == '__main__':
    # Rutas de los archivos crudos (capa Bronze), resueltas de forma
    # absoluta a partir de la ubicación de este script.
    archivo_pib = os.path.join(DIR_DATOS, 'retropolacion_1965_2024p.xlsx')
    archivo_wti = os.path.join(DIR_DATOS, 'petroleo_riesgo.csv')
    archivo_iee = os.path.join(DIR_DATOS, 'iee.csv')
    archivo_vab = os.path.join(DIR_DATOS, 'vab_provincial.csv')

    conexion_bd = sqlite3.connect(BD_PATH)

    # Cada tarea es independiente: (nombre, función, ruta, tabla destino)
    tareas = [
        ('PIB real',     procesar_pib_constante, archivo_pib, 'fact_macro_anual'),
        ('PIB nominal',  procesar_pib_corriente,  archivo_pib, 'fact_pib_nominal'),
        ('WTI/Riesgo',   limpiar_wti_embi,        archivo_wti, 'fact_indicadores_diarios'),
        ('IEE',          formatear_iee,           archivo_iee, 'fact_iee'),
        ('VAB regional', preparar_vab_regional,   archivo_vab, 'fact_vab'),
    ]

    print(f"Carpeta de datos: {DIR_DATOS}")
    print(f"Base de datos:    {BD_PATH}\n")

    exitosas = []
    fallidas = []

    try:
        for nombre, funcion, ruta, tabla in tareas:
            try:
                df_resultado = funcion(ruta)
                guardar_en_sqlite(df_resultado, tabla, conexion_bd)
                exitosas.append(tabla)
            except FileNotFoundError as e:
                print(f"   [OMITIDO] {nombre}: {e}")
                fallidas.append((nombre, ruta))
            except Exception as e:
                print(f"   [ERROR] {nombre} falló por un motivo distinto a archivo faltante: {e}")
                fallidas.append((nombre, ruta))

        print("\n--- RESUMEN DE EJECUCIÓN ---")
        print(f"Tablas cargadas correctamente: {len(exitosas)}/5 -> {exitosas}")

        if fallidas:
            print(f"\nTablas pendientes (archivo no encontrado u otro error): {len(fallidas)}")
            for nombre, ruta in fallidas:
                print(f"   - {nombre}: se esperaba en {ruta}")
            print(
                "\nColoca los archivos CSV/XLSX faltantes dentro de la carpeta "
                f"'{DIR_DATOS}' y vuelve a ejecutar este script. "
                "Las tablas ya cargadas no se pierden: cada una se guarda en "
                "cuanto su archivo de origen está disponible."
            )
        else:
            print("\n*** EJECUCIÓN FINALIZADA: Las 5 tablas están listas en la Capa Silver ***")

    finally:
        conexion_bd.close()

    # Código de salida útil si este script se llama desde otro proceso/CI:
    # 0 si las 5 tablas se cargaron, 1 si falta alguna.
    sys.exit(0 if not fallidas else 1)