from typing import Any, cast

import pandas as pd

from db import get_engine_palpites


def carregar_palpites():
    engine = get_engine_palpites()

    query = """
        SELECT *
        FROM simulations
        ORDER BY created_at DESC;
    """

    df = pd.read_sql(query, cast(Any, engine))
    return df
