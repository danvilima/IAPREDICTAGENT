import os

import streamlit as st
from sqlalchemy import create_engine


def get_secret_or_env(name: str):
    if name in st.secrets:
        return st.secrets[name]

    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} não encontrada.")

    return value


def get_engine_previsao():
    database_url = get_secret_or_env("DATABASE_URL_PREVISAO")
    return create_engine(database_url)


def get_engine_palpites():
    database_url = get_secret_or_env("DATABASE_URL_PALPITES")
    return create_engine(database_url)


# Compatibilidade com código antigo
def get_engine():
    return get_engine_previsao()

def get_raw_connection():
    import psycopg2
    database_url = get_secret_or_env("DATABASE_URL_PREVISAO")
    if database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(database_url)
