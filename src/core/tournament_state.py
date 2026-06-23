import pandas as pd
from typing import Dict, Any
from collections import defaultdict
from monte_carlo import preparar
import sys
import os

# Adiciona o diretório raiz ao path para importar modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from results_repository import get_all_real_results, FINISHED_STATUSES


def get_current_real_results() -> Dict[str, Any]:
    """
    Recupera o estado atual do torneio (os resultados reais já ocorridos) do Supabase.
    """
    res = {
        "champion": None,
        "runner_up": None,
        "third_place": None,
        "group_predictions": {},
        "third_place_predictions": {"matching": {}, "selected": []},
        "knockout_predictions": {},
    }

    try:
        df_results = get_all_real_results()
    except Exception:
        # Se falhar conexão com o banco ou tabela não existir
        return res

    if df_results.empty:
        return res

    finished = df_results[df_results["status_short"].isin(FINISHED_STATUSES)].copy()

    # 1. Resolver Fase de Grupos
    finished_groups = finished[finished["round"].str.contains("Group", na=False)].copy()

    if not finished_groups.empty:
        # Pega a letra do grupo (ex: "Group A - 1" -> "A")
        finished_groups["grupo_letra"] = finished_groups["round"].apply(
            lambda x: x.split("-")[0].replace("Group", "").strip()
        )

        for g, group_games in finished_groups.groupby("grupo_letra"):
            if len(group_games) == 6:  # Grupo decidido
                pontos = defaultdict(int)
                saldo = defaultdict(int)
                gols_pro = defaultdict(int)

                for _, row in group_games.iterrows():
                    t1, t2 = row["home_team_app"], row["away_team_app"]
                    g1, g2 = row["home_goals"], row["away_goals"]

                    gols_pro[t1] += g1
                    gols_pro[t2] += g2
                    saldo[t1] += g1 - g2
                    saldo[t2] += g2 - g1

                    if g1 > g2:
                        pontos[t1] += 3
                    elif g1 < g2:
                        pontos[t2] += 3
                    else:
                        pontos[t1] += 1
                        pontos[t2] += 1

                teams = list(pontos.keys())
                # Ordem: Pontos, Saldo, Gols Pró
                teams.sort(
                    key=lambda t: (pontos[t], saldo[t], gols_pro[t]), reverse=True
                )

                res["group_predictions"][g] = {"1st": teams[0], "2nd": teams[1]}

    # 2. Mata-Mata
    _, _, df_mata = preparar()
    df_mata["dt_time"] = pd.to_datetime(
        df_mata["match_date"]
        .astype(str)
        .str.cat(
            df_mata["match_time"].astype(str),
            sep=" ",
        )
    )
    df_mata_sorted = df_mata.sort_values("dt_time")

    finished_knockouts = finished[
        ~finished["round"].str.contains("Group", na=False)
    ].sort_values("match_date")

    # Mapeamento do nome do round da API-Football para a sigla do df_mata
    round_mapping = [
        ("Round of 32", "R32"),
        ("Round of 16", "R16"),
        ("Quarter-finals", "QF"),
        ("Semi-finals", "SF"),
        ("Final", "Final"),
        ("3rd Place Final", "3rd"),
    ]

    for round_api, round_cal in round_mapping:
        api_games = finished_knockouts[finished_knockouts["round"] == round_api]
        cal_games = df_mata_sorted[df_mata_sorted["round"] == round_cal]

        # Pareia por ordem cronológica (a ordem que as partidas ocorrem no round define qual slot Mxx é)
        limit = min(len(api_games), len(cal_games))
        for i in range(limit):
            api_row = api_games.iloc[i]
            cal_row = cal_games.iloc[i]

            match_id = cal_row["match_id"].replace("M", "")

            g1, g2 = api_row["home_goals"], api_row["away_goals"]
            p1, p2 = api_row["home_penalties"] or 0, api_row["away_penalties"] or 0

            winner_app = api_row["home_team_app"]
            loser_app = api_row["away_team_app"]

            if g2 > g1 or p2 > p1:
                winner_app = api_row["away_team_app"]
                loser_app = api_row["home_team_app"]

            res["knockout_predictions"][match_id] = winner_app

            if match_id == "104":
                res["champion"] = winner_app
                res["runner_up"] = loser_app
            elif match_id == "103":
                res["third_place"] = winner_app

    return res


def calculate_max_potential(
    user_row: Dict[str, Any], real_results: Dict[str, Any]
) -> int:
    """
    Avalia a pontuação máxima possível restante para o usuário.
    Esta função identifica quais palpites do usuário ainda são matematicamente possíveis
    no estado atual do torneio real e soma os pontos potenciais.
    """
    potential_score = 0

    if not real_results.get("champion"):
        potential_score += 3
    if not real_results.get("runner_up"):
        potential_score += 3
    if not real_results.get("third_place"):
        potential_score += 3

    user_knockout = user_row.get("knockout_predictions", {})
    real_knockout = real_results.get("knockout_predictions", {})

    for match_id, user_winner in user_knockout.items():
        if match_id in ["103", "104"]:
            continue

        real_winner = real_knockout.get(match_id)
        if not real_winner:
            potential_score += 2

    user_groups = user_row.get("group_predictions", {})
    real_groups = real_results.get("group_predictions", {})

    for group_name, user_positions in user_groups.items():
        real_positions = real_groups.get(group_name, {})
        if not real_positions.get("1st"):
            potential_score += 1
        if not real_positions.get("2nd"):
            potential_score += 1

    user_thirds = user_row.get("third_place_predictions", {}).get("selected", [])
    real_thirds = real_results.get("third_place_predictions", {}).get("selected", [])

    if len(real_thirds) < 8:
        remaining_slots = max(0, len(user_thirds) - len(real_thirds))
        potential_score += remaining_slots

    return potential_score
