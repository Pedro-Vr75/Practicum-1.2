import pandas as pd
import sqlite3
import os


# =========================================================
# MÓDULO DE INGESTA Y LIMPIEZA - FUENTES BCE
# =========================================================

def procesar_pib_constante(ruta_excel):
    print("-> Iniciando limpieza del PIB Real Anual...")
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
    print("-> Extrayendo PIB Nominal...")
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
    print("-> Procesando WTI y Riesgo País...")
    df_diario = pd.read_csv(ruta_csv)
    df_diario.rename(columns={'Período': 'fecha'}, inplace=True)
    df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
    return df_diario


def formatear_iee(ruta_csv):
    print("-> Normalizando IEE Mensual...")
    df_mensual = pd.read_csv(ruta_csv)
    df_mensual.columns = [c.lower() for c in df_mensual.columns]
    df_mensual['fecha'] = pd.to_datetime(df_mensual['fecha'], format='%Y-%m-%d')
    return df_mensual


def preparar_vab_regional(ruta_csv):
    print("-> Estructurando VAB Provincial...")
    df_prov = pd.read_csv(ruta_csv)
    df_prov.columns = [c.lower() for c in df_prov.columns]
    df_prov.rename(columns={'año': 'anio'}, inplace=True)
    return df_prov


# =========================================================
# CARGA A LA CAPA SILVER
# =========================================================

def guardar_en_sqlite(dataframe, tabla_destino, conx):
    dataframe.to_sql(tabla_destino, conx, if_exists='replace', index=False)
    print(f"   [OK] Tabla '{tabla_destino}' creada con éxito.")


# =========================================================
# FLUJO PRINCIPAL
# =========================================================

if __name__ == '__main__':
    # Directorios fijos
    archivo_pib = 'datos_macroentorno/retropolacion_1965_2024p.xlsx'
    archivo_wti = 'datos_macroentorno/petroleo_riesgo.csv'
    archivo_iee = 'datos_macroentorno/iee.csv'
    archivo_vab = 'datos_macroentorno/vab_provincial.csv'

    bd_path = 'pipeline_utpl.db'
    conexion_bd = sqlite3.connect(bd_path)

    try:
        # FASE 1: Procesamiento y Limpieza
        tabla_pib_real = procesar_pib_constante(archivo_pib)
        tabla_pib_nom = procesar_pib_corriente(archivo_pib)
        tabla_diaria = limpiar_wti_embi(archivo_wti)
        tabla_iee = formatear_iee(archivo_iee)
        tabla_vab = preparar_vab_regional(archivo_vab)

        print("\n--- INICIANDO CARGA A BASE DE DATOS ---")

        # FASE 2: Inserción en la BD
        guardar_en_sqlite(tabla_pib_real, 'fact_macro_anual', conexion_bd)
        guardar_en_sqlite(tabla_pib_nom, 'fact_pib_nominal', conexion_bd)
        guardar_en_sqlite(tabla_diaria, 'fact_indicadores_diarios', conexion_bd)
        guardar_en_sqlite(tabla_iee, 'fact_iee', conexion_bd)
        guardar_en_sqlite(tabla_vab, 'fact_vab', conexion_bd)

        print("\n*** EJECUCIÓN FINALIZADA: Las 5 tablas están listas en la Capa Silver ***")

    except Exception as error_pipeline:
        print(f"Se detectó un problema en la ejecución: {error_pipeline}")
    finally:
        conexion_bd.close()