# =============================================================
# RETO 1 — PIPELINE COMPLETO (ejecuta los 3 pasos en orden)
# =============================================================
import subprocess, sys

pasos = [
    ("Paso 1 — Exploración",  "01_exploracion.py"),
    ("Paso 2 — Limpieza",     "02_limpieza.py"),
    ("Paso 3 — Carga SQLite", "03_carga_sqlite.py"),
]

for nombre, script in pasos:
    print("\n" + "█" * 55)
    print(f"  {nombre}")
    print("█" * 55)
    r = subprocess.run([sys.executable, script], check=False)
    if r.returncode != 0:
        print(f"\n Error en {script}. Pipeline detenido.")
        sys.exit(1)

print("\n" + "█" * 55)
print(" Pipeline completado exitosamente")
print("█" * 55)
print("""
Archivo generado:
  data/instituciones_limpio.csv  <- Dataset limpio listo para Power BI
""")
