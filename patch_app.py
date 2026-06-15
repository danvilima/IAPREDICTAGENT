import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''from bandeiras import com_bandeira
from db import test_connection, get_engine'''
replacement1 = '''from bandeiras import com_bandeira, com_bandeira_html, obter_svg_data_uri
from db import test_connection, get_engine'''
content = content.replace(target1, replacement1)

target2 = '''        st.success(
            f"### 🥇 **CAMPEÃO:** {com_bandeira(podio.get('campeao', 'Unknown'))}"
        )
        c1, c2 = st.columns(2)
        c1.info(f"🥈 Vice: {com_bandeira(podio.get('vice', 'Unknown'))}")
        c2.warning(f"🥉 Terceiro: {com_bandeira(podio.get('terceiro', 'Unknown'))}")'''
replacement2 = '''        campeao = com_bandeira_html(podio.get('campeao', 'Unknown'))
        vice = com_bandeira_html(podio.get('vice', 'Unknown'))
        terceiro = com_bandeira_html(podio.get('terceiro', 'Unknown'))

        st.markdown(f"""
        <div style="background-color: rgba(40, 167, 69, 0.2); border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="margin:0;">🥇 <b>CAMPEÃO:</b> {campeao}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.markdown(f"""
        <div style="background-color: rgba(23, 162, 184, 0.2); border-left: 5px solid #17a2b8; padding: 15px; border-radius: 5px;">
            <h4 style="margin:0;">🥈 Vice: {vice}</h4>
        </div>
        """, unsafe_allow_html=True)
        c2.markdown(f"""
        <div style="background-color: rgba(255, 193, 7, 0.2); border-left: 5px solid #ffc107; padding: 15px; border-radius: 5px;">
            <h4 style="margin:0;">🥉 Terceiro: {terceiro}</h4>
        </div>
        """, unsafe_allow_html=True)'''
content = content.replace(target2, replacement2)

target3 = '''                for j in jogos_fase:
                    tc = com_bandeira(j['time_casa'])
                    tv = com_bandeira(j['time_visitante'])
                    gc = j['gols_casa']
                    gv = j['gols_visitante']
                    
                    texto_placar = f"{tc} **{gc} x {gv}** {tv}"
                    
                    if j['penaltis']:
                        pc = j['pen_casa']
                        pv = j['pen_visitante']
                        texto_placar += f" *(Pênaltis: {pc}-{pv})*"
                        
                    st.write(texto_placar)'''
replacement3 = '''                for j in jogos_fase:
                    tc = com_bandeira_html(j['time_casa'])
                    tv = com_bandeira_html(j['time_visitante'])
                    gc = j['gols_casa']
                    gv = j['gols_visitante']
                    
                    texto_placar = f"<div style='margin-bottom: 8px; font-size: 16px;'>{tc} &nbsp;<b>{gc} x {gv}</b>&nbsp; {tv}</div>"
                    
                    if j['penaltis']:
                        pc = j['pen_casa']
                        pv = j['pen_visitante']
                        texto_placar = texto_placar.replace('</div>', f" <i>(Pênaltis: {pc}-{pv})</i></div>")
                        
                    st.markdown(texto_placar, unsafe_allow_html=True)'''
content = content.replace(target3, replacement3)

target4 = '''        # Traduzindo colunas como mandatório na spec
        df_g['selecao'] = df_g['selecao'].apply(com_bandeira)
        cols_pt = ['grupo', 'posicao', 'selecao', 'jogos', 'vitorias', 'empates', 'derrotas', 'gols_pro', 'gols_contra', 'saldo_gols', 'pontos']
        df_g = df_g[cols_pt]
        
        for g, df_grupo in df_g.groupby('grupo'):
            with st.expander(f"Grupo {g}"):
                st.dataframe(df_grupo.drop('grupo', axis=1).style.highlight_max(subset=['pontos']), hide_index=True, use_container_width=True)'''
replacement4 = '''        # Traduzindo colunas como mandatório na spec
        df_g['Bandeira'] = df_g['selecao'].apply(obter_svg_data_uri)
        cols_pt = ['grupo', 'posicao', 'Bandeira', 'selecao', 'jogos', 'vitorias', 'empates', 'derrotas', 'gols_pro', 'gols_contra', 'saldo_gols', 'pontos']
        df_g = df_g[cols_pt]
        
        for g, df_grupo in df_g.groupby('grupo'):
            with st.expander(f"Grupo {g}"):
                st.dataframe(
                    df_grupo.drop('grupo', axis=1).style.highlight_max(subset=['pontos']), 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={"Bandeira": st.column_config.ImageColumn("Bandeira", width="small")}
                )'''
content = content.replace(target4, replacement4)

target5 = '''        st.markdown("---")
        st.markdown(f"### {com_bandeira(time1)} ⚔️ {com_bandeira(time2)}")'''
replacement5 = '''        st.markdown("---")
        st.markdown(f"<h3 style='text-align: center;'>{com_bandeira_html(time1)} ⚔️ {com_bandeira_html(time2)}</h3>", unsafe_allow_html=True)'''
content = content.replace(target5, replacement5)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
