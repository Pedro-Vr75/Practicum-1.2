
import pandas as pd
import sqlite3

CSV_LIMPIO = 'data/instituciones_limpio.csv'
DB_PATH    = 'amie_mineduc.db'

df = pd.read_csv(CSV_LIMPIO, encoding='utf-8')

try:
    from sqlalchemy import create_engine, text as sa_text
    engine = create_engine(f'sqlite:///{DB_PATH}')
    df.to_sql('instituciones', engine, if_exists='replace', index=False)
    def query(sql):
        with engine.connect() as conn:
            return pd.read_sql(sa_text(sql), conn)
except ImportError:
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql('instituciones', conn, if_exists='replace', index=False)
    def query(sql):
        with sqlite3.connect(DB_PATH) as c:
            return pd.read_sql_query(sql, c)

print(f"Base de datos SQLite lista: {DB_PATH}")
