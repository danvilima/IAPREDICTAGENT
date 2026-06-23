from typing import Dict, Any, List
import pandas as pd

def parse_real_results(real_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função utilitária para garantir que os resultados reais estejam no mesmo
    formato esperado pelas predições do usuário para fácil comparação.
    """
    return real_data

def calculate_user_score(user_row: pd.Series, real_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula a pontuação de um usuário com base nas regras:
    - Grupos: 1 pt por acerto (1st, 2nd, e 3rd classificados)
    - Mata-mata: 2 pts por avanço correto
    - Finais: 3 pts para Campeão, Vice e Terceiro
    """
    score_grupos = 0
    score_mata_mata = 0
    score_finais = 0
    
    # 1. PONTUAÇÃO DE GRUPOS (1 pt cada)
    real_groups = real_results.get('group_predictions', {})
    user_groups = user_row.get('group_predictions', {})
    
    for group_name, real_positions in real_groups.items():
        user_group = user_groups.get(group_name, {})
        # Verifica o 1º lugar
        if real_positions.get('1st') and real_positions.get('1st') == user_group.get('1st'):
            score_grupos += 1
        # Verifica o 2º lugar
        if real_positions.get('2nd') and real_positions.get('2nd') == user_group.get('2nd'):
            score_grupos += 1

    # Terceiros lugares (classificados)
    real_thirds = real_results.get('third_place_predictions', {}).get('selected', [])
    user_thirds = user_row.get('third_place_predictions', {}).get('selected', [])
    
    # Converte para dicionário {Grupo: Seleção} para checagem rápida
    real_thirds_dict = {item[0]: item[1] for item in real_thirds} if isinstance(real_thirds, list) else {}
    user_thirds_dict = {item[0]: item[1] for item in user_thirds} if isinstance(user_thirds, list) else {}
    
    for group_name, selection in real_thirds_dict.items():
        if user_thirds_dict.get(group_name) == selection:
            score_grupos += 1

    # 2. PONTUAÇÃO DE MATA-MATA (2 pts cada)
    real_knockout = real_results.get('knockout_predictions', {})
    user_knockout = user_row.get('knockout_predictions', {})
    
    # Vamos considerar que os jogos do mata-mata (exceto final e disputa de 3o) dão 2 pontos
    # A final é o jogo 104, disputa de 3o é o 103 (por dedução)
    # Se houver pontuação separada pro vencedor da disputa de 3º, tratamos em "score_finais"
    for match_id, real_winner in real_knockout.items():
        # Ignora as finais no loop de 2 pontos (vamos usar as colunas diretas para dar 3 pontos)
        # Se os campos de 'knockout_predictions' contiverem as decisões, não daremos pontos duplos.
        if match_id in ['103', '104']:
            continue
            
        user_winner = user_knockout.get(match_id)
        if real_winner and real_winner == user_winner:
            score_mata_mata += 2

    # 3. PONTUAÇÃO DAS FINAIS (3 pts cada)
    if real_results.get('champion') and real_results.get('champion') == user_row.get('champion'):
        score_finais += 3
        
    if real_results.get('runner_up') and real_results.get('runner_up') == user_row.get('runner_up'):
        score_finais += 3
        
    if real_results.get('third_place') and real_results.get('third_place') == user_row.get('third_place'):
        score_finais += 3

    total_score = score_grupos + score_mata_mata + score_finais
    
    return {
        'user_name': user_row.get('user_name'),
        'total_score': total_score,
        'score_finais': score_finais,
        'score_mata_mata': score_mata_mata,
        'score_grupos': score_grupos,
        'created_at': user_row.get('created_at'),
        'palpites_corretos': (score_grupos // 1) + (score_mata_mata // 2) + (score_finais // 3),
    }

def process_ranking(df_simulations: pd.DataFrame, real_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Recebe o dataframe com os palpites, aplica o cálculo e ordena o ranking
    com base nas rigorosas regras de desempate.
    """
    scores_list = []
    for _, row in df_simulations.iterrows():
        scores_list.append(calculate_user_score(row, real_results))
        
    df_scores = pd.DataFrame(scores_list)
    
    if df_scores.empty:
        return df_scores
        
    # Ordenação (Tie-breakers):
    # 1. Maior pontuação total (ASC=False)
    # 2. Maior pontuação em finais (ASC=False)
    # 3. Maior pontuação em mata-mata (ASC=False)
    # 4. Maior pontuação em grupos (ASC=False)
    # 5. Data do palpite (ASC=True) -> quem fez primeiro
    # 6. Ordem alfabética do user_name (ASC=True)
    
    # O sort_values do pandas permite listas booleanas em 'ascending'
    df_ranking = df_scores.sort_values(
        by=['total_score', 'score_finais', 'score_mata_mata', 'score_grupos', 'created_at', 'user_name'],
        ascending=[False, False, False, False, True, True]
    )
    
    df_ranking.insert(0, 'posicao', range(1, len(df_ranking) + 1))
    
    return df_ranking
