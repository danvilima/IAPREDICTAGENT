from typing import Any, cast

import pandas as pd

from db import get_engine_previsao


def carregar_probabilidades():
    engine = get_engine_previsao()

    query = """
        SELECT *
        FROM gold_probabilidades_copa
        ORDER BY prob_campea DESC;
    """

    df = pd.read_sql(query, cast(Any, engine))
    return df
