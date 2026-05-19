
import pandas as pd

CSV_PATH = 'data/2_MINEDUC_RegistrosAdministrativos_2023-2024Inicio.csv'

print("Cargando CSV...")
df = pd.read_csv(CSV_PATH, sep=';', encoding='latin-1')
print(f"Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
print(f"Nulos totales: {df.isnull().sum().sum()}")
print(f"Duplicados por AMIE: {df.duplicated(subset=['AMIE']).sum()}")
print(" Exploración completada.")
