"""
db.py — Conexión a Oracle usando python-oracledb en modo "thin"
(no necesita instalar el Oracle Instant Client aparte).

Ajusta USER, PASSWORD y DSN a tus datos reales de conexión.
"""
import oracledb

USER = "admin"
PASSWORD = "pwdadmin"
DSN = "localhost:1521/XEPDB1"   # host:puerto/servicio -- ajusta si el tuyo es distinto


def get_connection():
    return oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
