
import pandas as pd
import os

CSV_PATH   = 'data/2_MINEDUC_RegistrosAdministrativos_2023-2024Inicio.csv'
SALIDA_CSV = 'data/instituciones_limpio.csv'

df = pd.read_csv(CSV_PATH, sep=';', encoding='latin-1')
print(f"Dataset cargado: {df.shape[0]} filas x {df.shape[1]} columnas")

# T1 — Renombrar columnas
RENAME = {
    'Año lectivo'              : 'anio_lectivo',
    'AMIE'                     : 'cod_amie',
    'Nombre_Institución'       : 'nombre_institucion',
    'Zona'                     : 'zona',
    'Provincia'                : 'provincia',
    'Cod_Provincia'            : 'cod_provincia',
    'Cantón'                   : 'canton',
    'Cod_Cantón'               : 'cod_canton',
    'Parroquia'                : 'parroquia',
    'Cod_Parroquia'            : 'cod_parroquia',
    'Escolarización'           : 'escolarizacion',
    'Tipo Educación'           : 'tipo_educacion',
    'Nivel Educación'          : 'nivel_educacion',
    'Sostenimiento'            : 'sostenimiento',
    'Área'                     : 'area',
    'Régimen Escolar'          : 'regimen_escolar',
    'Jurisdicción'             : 'jurisdiccion',
    'Modalidad'                : 'modalidad',
    'Jornada'                  : 'jornada',
    'Tenencia Inmueble Edificio': 'tenencia_inmueble',
    'Acceso Edificio'          : 'acceso_edificio',
    'Docentes Femenino'        : 'docentes_f',
    'Docentes Masculino'       : 'docentes_m',
    'Total Docentes'           : 'total_docentes',
    'Administrativos Femenino' : 'admin_f',
    'Administrativos Masculino': 'admin_m',
    'Total Administrativos'    : 'total_admin',
    'Estudiantes Femenino'     : 'estudiantes_f',
    'Estudiantes Masculino'    : 'estudiantes_m',
    'Total Estudiantes'        : 'total_estudiantes',
}
df = df.rename(columns=RENAME)
print("[T1] Columnas renombradas.")

# T2 — Rellenar nulos con 0
cols_num = ['total_docentes','total_estudiantes','estudiantes_f','estudiantes_m',
            'docentes_f','docentes_m','total_admin','admin_f','admin_m']
cols_num = [c for c in cols_num if c in df.columns]
df[cols_num] = df[cols_num].fillna(0).astype(int)
print("[T2] Nulos rellenados con 0.")

# T3 — Eliminar duplicados
antes = len(df)
df = df.drop_duplicates(subset=['cod_amie', 'anio_lectivo'])
print(f"[T3] Duplicados eliminados: {antes - len(df)}")

# T4 — Marcar inconsistencias
df['flag_inconsistencia'] = (df['estudiantes_f'] + df['estudiantes_m']) != df['total_estudiantes']
print(f"[T4] Inconsistencias marcadas: {df['flag_inconsistencia'].sum()}")

# Guardar solo el CSV limpio
os.makedirs('data', exist_ok=True)
df.to_csv(SALIDA_CSV, index=False, encoding='utf-8')
print(f"\nCSV limpio guardado en '{SALIDA_CSV}'")
print(f"   {df.shape[0]} filas x {df.shape[1]} columnas")
