import os
path = 'src/bandeiras.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

append_code = '''
def com_bandeira_md(selecao: str) -> str:
    uri = obter_svg_data_uri(selecao)
    if uri:
        # Markdown não permite controlar width nativamente facilmente, mas para bandeiras vai funcionar. 
        # Outra forma é usar tag <img> HTML, mas aí st.success não renderiza.
        # Vamos usar a tag <img> HTML e, se a UI não renderizar, o markdown fallback:
        # Mas streamlit suporta HTML em markdown se unsafe_allow_html=True.
        # Mas st.success não tem unsafe_allow_html.
        pass
    return com_bandeira(selecao)
'''
