import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

# Get connection string directly to make sure we use the right one
database_url = "postgresql://postgres:%24Rayan77%24Crvg@db.umpwzetgfgjtiihewbyr.supabase.co:5432/postgres"
engine = create_engine(database_url)

sql_create = """
-- 1. Criação da tabela api_sync_log
CREATE TABLE IF NOT EXISTS api_sync_log (
    sync_key VARCHAR(100) PRIMARY KEY,
    last_sync TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Criação da tabela real_results
CREATE TABLE IF NOT EXISTS real_results (
    fixture_id INT PRIMARY KEY,
    league_id INT,
    season INT,
    match_date TIMESTAMPTZ,
    status_short VARCHAR(20),
    status_long VARCHAR(100),
    home_team_id INT,
    away_team_id INT,
    home_team_api VARCHAR(100),
    away_team_api VARCHAR(100),
    home_team_app VARCHAR(100),
    away_team_app VARCHAR(100),
    home_goals INT,
    away_goals INT,
    home_penalties INT,
    away_penalties INT,
    round VARCHAR(100),
    group_name VARCHAR(50),
    phase VARCHAR(50),
    api_raw_json JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    synced_at TIMESTAMPTZ DEFAULT NOW()
);
"""

try:
    with engine.connect() as conn:
        conn.execute(text(sql_create))
        conn.commit()
    print("Tabelas criadas com sucesso.")
except Exception as e:
    print(f"Erro ao criar tabelas: {e}")
    sys.exit(1)

# Validação solicitada
try:
    df_results = pd.read_sql("SELECT * FROM real_results LIMIT 5;", engine)
    df_sync = pd.read_sql("SELECT * FROM api_sync_log LIMIT 5;", engine)
    print("\n--- SELECT * FROM real_results LIMIT 5 ---")
    print(df_results)
    print("\n--- SELECT * FROM api_sync_log LIMIT 5 ---")
    print(df_sync)
except Exception as e:
    print(f"Erro na validação: {e}")
