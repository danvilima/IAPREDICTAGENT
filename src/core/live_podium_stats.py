import pandas as pd
from typing import Any

def calcular_estatisticas_podio(df_probs: pd.DataFrame, df_real_results: pd.DataFrame) -> pd.DataFrame:
    stats = {}
    
    # Initialize all teams found in base probabilities
    for selecao in df_probs['selecao']:
        stats[selecao] = {
            'selecao': selecao,
            'pontos': 0.0,
            'jogos': 0.0,
            'gols_pro': 0.0,
            'gols_contra': 0.0,
            'saldo_gols': 0.0,
            'fator_performance': 1.0
        }
        
    # Process real results if not empty
    if not df_real_results.empty:
        # Pega jogos com status finalizado ou ao vivo
        # Consideramos 'FT', 'AET', 'PEN' como peso 1, e 'LIVE' como peso 0.5
        finished_statuses = ["FT", "AET", "PEN"]
        live_statuses = ["LIVE"]
        
        valid_matches = df_real_results[df_real_results['status_short'].isin(finished_statuses + live_statuses)]
        
        for _, row in valid_matches.iterrows():
            t1 = row['home_team_app']
            t2 = row['away_team_app']
            g1 = row['home_goals'] or 0
            g2 = row['away_goals'] or 0
            status = row['status_short']
            
            peso = 1.0 if status in finished_statuses else 0.5
            
            for t in [t1, t2]:
                if t not in stats:
                    stats[t] = {
                        'selecao': t, 'pontos': 0.0, 'jogos': 0.0,
                        'gols_pro': 0.0, 'gols_contra': 0.0, 'saldo_gols': 0.0,
                        'fator_performance': 1.0
                    }
                    
            stats[t1]['jogos'] += peso
            stats[t2]['jogos'] += peso
            stats[t1]['gols_pro'] += g1 * peso
            stats[t2]['gols_pro'] += g2 * peso
            stats[t1]['gols_contra'] += g2 * peso
            stats[t2]['gols_contra'] += g1 * peso
            stats[t1]['saldo_gols'] += (g1 - g2) * peso
            stats[t2]['saldo_gols'] += (g2 - g1) * peso
            
            if g1 > g2:
                stats[t1]['pontos'] += 3.0 * peso
            elif g1 < g2:
                stats[t2]['pontos'] += 3.0 * peso
            else:
                stats[t1]['pontos'] += 1.0 * peso
                stats[t2]['pontos'] += 1.0 * peso

    # Calculate Performance Factor
    # A simple dynamic factor based on user's suggestion:
    # fator = 1.0 + (pontos * 0.1) + (saldo_gols * 0.05)
    for t, data in stats.items():
        # Minimum factor of 0.1 so teams don't hit negative 0 chance
        data['fator_performance'] = max(0.1, 1.0 + (data['pontos'] * 0.1) + (data['saldo_gols'] * 0.05))
        
    df_stats = pd.DataFrame(list(stats.values()))
    
    # Merge
    df_merged = pd.merge(df_probs, df_stats, on='selecao', how='left')
    
    # Calculate probabilities
    df_merged['chance_campeao'] = df_merged['prob_campea'] * df_merged['fator_performance']
    df_merged['chance_vice'] = (df_merged['prob_final'] - df_merged['prob_campea']) * df_merged['fator_performance']
    df_merged['chance_terceiro'] = (df_merged['prob_semi'] - df_merged['prob_final']) * df_merged['fator_performance']
    
    # Clip and normalize
    for col in ['chance_campeao', 'chance_vice', 'chance_terceiro']:
        df_merged[col] = df_merged[col].clip(lower=0).fillna(0)
        total = df_merged[col].sum()
        if total > 0:
            df_merged[col] = df_merged[col] / total
        else:
            df_merged[col] = 0.0
            
    return df_merged
