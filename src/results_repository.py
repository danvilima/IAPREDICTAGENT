import json
import pandas as pd
from typing import List, Dict, Any, cast
from sqlalchemy import text
from db import get_engine_palpites

FINISHED_STATUSES = ["FT", "AET", "PEN"]

API_TO_APP_NAMES = {
    "Brazil": "🇧🇷 Brasil",
    "Argentina": "🇦🇷 Argentina",
    "France": "🇫🇷 França",
    "Spain": "🇪🇸 Espanha",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra",
    "Germany": "🇩🇪 Alemanha",
    "Portugal": "🇵🇹 Portugal",
    "Netherlands": "🇳🇱 Holanda",
    "Italy": "🇮🇹 Itália",
    "Croatia": "🇭🇷 Croácia",
    "Belgium": "🇧🇪 Bélgica",
    "Uruguay": "🇺🇾 Uruguai",
    "Colombia": "🇨🇴 Colômbia",
    "USA": "🇺🇸 Estados Unidos",
    "United States": "🇺🇸 Estados Unidos",
    "Mexico": "🇲🇽 México",
    "Senegal": "🇸🇳 Senegal",
    "Morocco": "🇲🇦 Marrocos",
    "Japan": "🇯🇵 Japão",
    "South Korea": "🇰🇷 Coreia do Sul",
    "Iran": "🇮🇷 Irã",
    "Australia": "🇦🇺 Austrália",
    "Switzerland": "🇨🇭 Suíça",
    "Denmark": "🇩🇰 Dinamarca",
    "Sweden": "🇸🇪 Suécia",
    "Serbia": "🇷🇸 Sérvia",
    "Poland": "🇵🇱 Polônia",
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia",
    "Tunisia": "🇹🇳 Tunísia",
    "Cape Verde": "🇨🇻 Cabo Verde",
    "DR Congo": "🇨🇩 RD Congo",
    "Czech Republic": "🇨🇿 República Tcheca",
    "Ecuador": "🇪🇨 Equador",
    "Qatar": "🇶🇦 Catar",
    "Saudi Arabia": "🇸🇦 Arábia Saudita",
    "Cameroon": "🇨🇲 Camarões",
    "Ghana": "🇬🇭 Gana",
    "Costa Rica": "🇨🇷 Costa Rica",
    "Panama": "🇵🇦 Panamá",
    "Haiti": "🇭🇹 Haiti",
    "Iraq": "🇮🇶 Iraque",
    "Egypt": "🇪🇬 Egito",
    "Canada": "🇨🇦 Canadá",
    "Algeria": "🇩🇿 Argélia",
    "Uzbekistan": "🇺🇿 Uzbequistão",
    "Turkey": "🇹🇷 Turquia",
    "South Africa": "🇿🇦 África do Sul",
    "New Zealand": "🇳🇿 Nova Zelândia",
    "Norway": "🇳🇴 Noruega",
    "Ivory Coast": "🇨🇮 Costa do Marfim",
    "Bosnia and Herzegovina": "🇧🇦 Bósnia",
    "Paraguay": "🇵🇾 Paraguai",
    "Jordan": "🇯🇴 Jordânia",
    "Curaçao": "🇨🇼 Curaçao",
    "Austria": "🇦🇹 Áustria",
}


def translate_team(api_name: str) -> str:
    return API_TO_APP_NAMES.get(api_name, api_name)


def get_last_sync_time(sync_key: str):
    engine = get_engine_palpites()
    query = text("SELECT last_sync FROM api_sync_log WHERE sync_key = :k")
    with engine.connect() as conn:
        result = conn.execute(query, {"k": sync_key}).fetchone()
        if result:
            return result[0]
    return None


def update_sync_time(sync_key: str):
    engine = get_engine_palpites()
    query = text(
        """
        INSERT INTO api_sync_log (sync_key, last_sync, updated_at)
        VALUES (:k, NOW(), NOW())
        ON CONFLICT (sync_key) DO UPDATE SET
            last_sync = EXCLUDED.last_sync,
            updated_at = EXCLUDED.updated_at
    """
    )
    with engine.connect() as conn:
        conn.execute(query, {"k": sync_key})
        conn.commit()


def upsert_fixtures(fixtures_data: List[Dict[str, Any]]) -> bool:
    engine = get_engine_palpites()
    new_finished = False

    query_existing = text("SELECT fixture_id, status_short FROM real_results")
    with engine.connect() as conn:
        existing = conn.execute(query_existing).fetchall()
        existing_status = {row[0]: row[1] for row in existing}

    upsert_sql = text(
        """
        INSERT INTO real_results (
            fixture_id, league_id, season, match_date, status_short, status_long, 
            home_team_id, away_team_id, home_team_api, away_team_api, 
            home_team_app, away_team_app, home_goals, away_goals, 
            home_penalties, away_penalties, round, api_raw_json, updated_at, synced_at
        ) VALUES (
            :f_id, :l_id, :sea, :md, :ss, :sl,
            :ht_id, :at_id, :ht_api, :at_api,
            :ht_app, :at_app, :hg, :ag,
            :hp, :ap, :rnd, :raw, NOW(), NOW()
        )
        ON CONFLICT (fixture_id) DO UPDATE SET
            match_date = EXCLUDED.match_date,
            status_short = EXCLUDED.status_short,
            status_long = EXCLUDED.status_long,
            home_team_api = EXCLUDED.home_team_api,
            away_team_api = EXCLUDED.away_team_api,
            home_team_app = EXCLUDED.home_team_app,
            away_team_app = EXCLUDED.away_team_app,
            home_goals = EXCLUDED.home_goals,
            away_goals = EXCLUDED.away_goals,
            home_penalties = EXCLUDED.home_penalties,
            away_penalties = EXCLUDED.away_penalties,
            round = EXCLUDED.round,
            api_raw_json = EXCLUDED.api_raw_json,
            updated_at = NOW(),
            synced_at = EXCLUDED.synced_at
    """
    )

    with engine.begin() as conn:
        for f in fixtures_data:
            f_id = f["fixture"]["id"]
            status_short = f["fixture"]["status"]["short"]

            if status_short in FINISHED_STATUSES:
                if existing_status.get(f_id) not in FINISHED_STATUSES:
                    new_finished = True

            home_api = f["teams"]["home"]["name"]
            away_api = f["teams"]["away"]["name"]

            params = {
                "f_id": f_id,
                "l_id": f["league"]["id"],
                "sea": f["league"]["season"],
                "md": f["fixture"]["date"],
                "ss": status_short,
                "sl": f["fixture"]["status"]["long"],
                "ht_id": f["teams"]["home"]["id"],
                "at_id": f["teams"]["away"]["id"],
                "ht_api": home_api,
                "at_api": away_api,
                "ht_app": translate_team(home_api),
                "at_app": translate_team(away_api),
                "hg": f["goals"]["home"],
                "ag": f["goals"]["away"],
                "hp": f["score"]["penalty"]["home"],
                "ap": f["score"]["penalty"]["away"],
                "rnd": f["league"]["round"],
                "raw": json.dumps(f),
            }
            conn.execute(upsert_sql, params)

    return new_finished


def get_all_real_results() -> pd.DataFrame:
    engine = get_engine_palpites()

    query = """
        SELECT *
        FROM real_results
        ORDER BY match_date ASC;
    """

    with engine.connect() as conn:
        return pd.read_sql_query(query, cast(Any, conn))
