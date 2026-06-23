import sys
import os
import pandas as pd
from sqlalchemy import create_engine

os.environ["DATABASE_URL_PALPITES"] = "postgresql://postgres:%24Rayan77%24Crvg@db.umpwzetgfgjtiihewbyr.supabase.co:5432/postgres"

engine = create_engine(os.environ["DATABASE_URL_PALPITES"])
query = "SELECT * FROM simulations LIMIT 1;"
df = pd.read_sql(query, engine)

print("Columns:", df.columns)
if not df.empty:
    print("group_predictions:", df.iloc[0].get("group_predictions"))
    print("knockout_predictions:", df.iloc[0].get("knockout_predictions"))
    print("champion:", df.iloc[0].get("champion"))
