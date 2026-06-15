import re
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
old_block = '''    query = """
        SELECT selecao, prob_grupo, prob_oitavas, prob_quartas, prob_semi, prob_final, prob_campea
        FROM gold_probabilidades_copa
        ORDER BY prob_campea DESC
        LIMIT 12;
    """
    df = pd.read_sql(query, engine)'''
new_block = '''    query = """
        SELECT selecao, prob_grupo, prob_oitavas, prob_quartas, prob_semi, prob_final, prob_campea
        FROM gold_probabilidades_copa
        ORDER BY prob_campea DESC
        LIMIT 12;
    """
    from sqlalchemy import text
    with engine.connect() as conexao:
        df = pd.read_sql(text(query), conexao)'''
content = content.replace(old_block, new_block)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)