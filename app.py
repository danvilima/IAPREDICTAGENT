from textwrap import dedent
from typing import Any, cast
import os
import sys

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Injetando o src no Path para imports locais
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Ponte de cloud secrets vs local environment
try:
    if "DATABASE_URL" in st.secrets and "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
except Exception:
    pass

from db import get_engine
from previsao import carregar_modelos, prever_jogo
from monte_carlo import preparar, simular_torneio_detalhado
from bandeiras import com_bandeira, com_bandeira_html, obter_svg_data_uri


st.set_page_config(page_title="IAPredict — Copa 2026", layout="wide")

TOP_N = 12


# ==========================================
# CACHING DE MODELOS E CONEXÕES
# ==========================================
@st.cache_resource
def injetar_dependencias():
    engine = get_engine()
    carregar_modelos()
    df_jogos, df_grupos, df_mata = preparar()
    return engine, df_jogos, df_grupos, df_mata


@st.cache_data(ttl=3600)
def buscar_probabilidades():
    engine = get_engine()

    query = f"""
        SELECT 
            selecao, 
            prob_grupo, 
            prob_oitavas, 
            prob_quartas, 
            prob_semi, 
            prob_final, 
            prob_campea
        FROM gold_probabilidades_copa
        ORDER BY prob_campea DESC
        LIMIT {TOP_N};
    """

    with engine.connect() as conexao:
        df = pd.read_sql_query(query, cast(Any, conexao))

    # Keep base names in the raw dataframe, we'll format them on demand
    return df


@st.cache_data(ttl=3600)
def buscar_probabilidades_completas():
    engine = get_engine()
    query = """
        SELECT 
            selecao, 
            prob_grupo, 
            prob_oitavas, 
            prob_quartas, 
            prob_semi, 
            prob_final, 
            prob_campea
        FROM gold_probabilidades_copa
        ORDER BY prob_campea DESC;
    """
    with engine.connect() as conexao:
        df = pd.read_sql_query(query, cast(Any, conexao))
    return df


engine, df_jogos, df_grupos, df_mata = injetar_dependencias()


from streamlit_option_menu import option_menu
from results_repository import get_last_sync_time

# ==========================================
# GESTÃO DE TEMA E SIDEBAR NAVIGATION
# ==========================================

if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "🌙 Escuro"

def aplicar_tema(theme_choice: str):
    if theme_choice == "☀️ Claro":
        bg_main = "#F8FAFC"
        bg_card = "#FFFFFF"
        bg_sidebar = "#EEF2FF"
        text_main = "#0F172A"
        text_muted = "#475569"
        border = "#CBD5E1"
        primary = "#4F46E5"
        accent = "#2563EB"
    else:
        bg_main = "#0B1020"
        bg_card = "#1E1B3A"
        bg_sidebar = "#17162E"
        text_main = "#F8FAFC"
        text_muted = "#CBD5E1"
        border = "#334155"
        primary = "#6366F1"
        accent = "#60A5FA"

    css = f"""
<style>
    .stApp {{
        background-color: {bg_main};
        color: {text_main};
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
    }}
    
    .sidebar-title {{
        font-size: 24px;
        font-weight: bold;
        color: {text_main};
        margin-bottom: 0px;
    }}
    .sidebar-subtitle {{
        font-size: 14px;
        color: {text_muted};
        margin-bottom: 20px;
    }}
    .status-box {{
        background-color: {bg_card};
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 13px;
        border: 1px solid {border};
    }}
    .status-item {{
        margin: 5px 0;
        color: {text_main};
    }}
    
    /* Botão de abrir a sidebar (menu) */
    [data-testid="collapsedControl"] {{
        top: 18px !important;
        left: 18px !important;
        width: 82px !important;
        height: 42px !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg, {primary}, {accent}) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        box-shadow: 0 0 18px rgba(0, 0, 0, 0.2) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out !important;
        z-index: 999999 !important;
    }}

    [data-testid="collapsedControl"]:hover {{
        transform: scale(1.06);
        box-shadow: 0 0 24px rgba(0, 0, 0, 0.3) !important;
    }}

    [data-testid="collapsedControl"] svg {{
        display: none !important;
    }}

    [data-testid="collapsedControl"]::after {{
        content: "☰ MENU";
        color: white;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.8px;
        line-height: 1;
    }}

    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {{
        border-radius: 12px !important;
        background: rgba(128, 128, 128, 0.08) !important;
        border: 1px solid rgba(128, 128, 128, 0.15) !important;
        transition: all 0.2s ease-in-out !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover {{
        background: rgba(128, 128, 128, 0.25) !important;
    }}

    /* Estilos do Ranking e Cards Globais */
    .ranking-card {{
        background-color: {bg_card};
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid {border};
        border-left: 5px solid {primary};
        color: {text_main};
    }}
    .podium-card {{
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        text-align: center;
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }}
    .gold-card {{ background: linear-gradient(135deg, #FFD700, #DAA520); color: #111; border: 2px solid #FFF8DC; }}
    .silver-card {{ background: linear-gradient(135deg, #E0E0E0, #A9A9A9); color: #111; border: 2px solid #F8F8FF; }}
    .bronze-card {{ background: linear-gradient(135deg, #CD7F32, #8B4513); color: #fff; border: 2px solid #FFDAB9; }}
    .score-big {{ font-size: 32px; font-weight: 900; margin: 10px 0; color: {text_main}; }}
    .ranking-meta {{ font-size: 14px; opacity: 0.95; margin: 4px 0; color: {text_muted}; }}
    .other-rank-name {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; }}
    .flex-row {{ display: flex; justify-content: space-between; align-items: center; }}

    .summary-card {{
        background-color: {bg_card};
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid {border};
        color: {text_main};
    }}
    .summary-main {{
        font-size: 18px;
        margin-bottom: 15px;
    }}
    .summary-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 15px;
        text-align: center;
    }}
    .summary-grid div {{
        background-color: {bg_main};
        padding: 10px;
        border-radius: 8px;
        border: 1px solid {border};
    }}
    .summary-grid span {{
        display: block;
        font-size: 12px;
        color: {text_muted};
    }}
    .summary-grid strong {{
        display: block;
        font-size: 20px;
        color: {primary};
    }}
    .summary-second {{
        font-size: 15px;
        padding: 10px;
        background-color: {bg_main};
        border-radius: 8px;
        border-left: 4px solid {border};
        color: {text_main};
    }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


with st.sidebar:
    st.markdown(
        '<p class="sidebar-title">🏆 IAPredict Copa 2026</p>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sidebar-subtitle">Bolão inteligente + estatísticas em tempo real</p>',
        unsafe_allow_html=True,
    )

    theme_choice = st.radio(
        "Tema",
        ["🌙 Escuro", "☀️ Claro"],
        horizontal=True,
        index=0 if st.session_state.theme_choice == "🌙 Escuro" else 1
    )
    st.session_state.theme_choice = theme_choice

    aplicar_tema(st.session_state.theme_choice)

    if st.session_state.theme_choice == "☀️ Claro":
        nav_hover = "#E0E7FF"
        nav_selected = "#C7D2FE"
        icon_color = "#0F172A"
        nav_text = "#0F172A"
    else:
        nav_hover = "#242442"
        nav_selected = "#4b4b9e"
        icon_color = "white"
        nav_text = "white"

    selected = option_menu(
        menu_title=None,
        options=[
            "Ranking",
            "Probabilidades Pré-Copa",
            "Explorador",
            "Estatísticas Tempo Real",
        ],
        icons=["award-fill", "trophy-fill", "search", "graph-up-arrow"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": icon_color, "font-size": "18px"},
            "nav-link": {
                "color": nav_text,
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": nav_hover,
            },
            "nav-link-selected": {"background-color": nav_selected, "color": nav_text},
        },
    )

    page_map = {
        "Ranking": "Ranking dos Palpites",
        "Probabilidades Pré-Copa": "Probabilidades Pré-computadas",
        "Explorador": "Explorador de partidas",
        "Estatísticas Tempo Real": "Estatísticas em tempo real",
    }

    page = page_map[selected]

    st.markdown("---")

    # Block "📡 Status"
    st.markdown("### 📡 Status")
    st.markdown(
        """
    <div class="status-box">
        <div class="status-item">✅ Sistema ativo</div>
        <div class="status-item">✅ Supabase conectado</div>
        <div class="status-item">✅ Resultados sincronizados</div>
    </div>
    """.replace(
            "\n", ""
        ),
        unsafe_allow_html=True,
    )

    # Block "Última atualização"
    st.markdown("### ⏱️ Última atualização")
    try:
        last_sync = get_last_sync_time("fixtures_today")
        if last_sync:
            st.info(last_sync.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            st.info("Aguardando sincronização")
    except Exception:
        st.info("Aguardando sincronização")

    # Block "👀 Visão rápida"
    st.markdown("### 👀 Visão rápida")

    participants = "--"
    games_synced = "--"

    try:
        from palpites import carregar_palpites
        from results_repository import get_all_real_results

        df_p = carregar_palpites()
        if not df_p.empty:
            participants = str(len(df_p))

        df_r = get_all_real_results()
        if not df_r.empty:
            games_synced = str(len(df_r))
    except Exception:
        pass

    st.markdown(
        f"""
    <div class="status-box">
        <div class="status-item">👥 Participantes: {participants}</div>
        <div class="status-item">⚽ Jogos: {games_synced}</div>
        <div class="status-item">🔄 Sync: Ativo</div>
    </div>
    """.replace(
            "\n", ""
        ),
        unsafe_allow_html=True,
    )


# ==========================================
# PÁGINA 1: PROBABILIDADES ESTÁVEIS
# ==========================================
if page == "Probabilidades Pré-computadas":
    st.title("🏆 Favoritas da Copa (Machine Learning)")

    st.markdown(
        "Projeções oficiais consolidadas após simulação massiva de Monte Carlo "
        "(60.000 Jogos). O modelo leva em consideração força recente de Elo e "
        "as complexidades de chaveamento da competição."
    )

    df_probs = buscar_probabilidades()

    # Prepara DF para o Altair (using emojis for chart)
    df_plot = df_probs.copy()
    df_plot["Ícone"] = df_plot["selecao"].apply(obter_svg_data_uri)
    df_plot["Chances de Título (%)"] = df_plot["prob_campea"] * 100

    # Gráfico de barras
    bars = (
        alt.Chart(df_plot)
        .mark_bar(color="#5c92ff")
        .encode(
            x=alt.X(
                "selecao:N", sort="-y", title="Seleção", axis=alt.Axis(labelAngle=-45)
            ),
            y=alt.Y("Chances de Título (%):Q", title="Probabilidade (%)"),
            tooltip=["selecao", "Chances de Título (%)"],
        )
    )

    # Imagens (Bandeiras SVG)
    images = (
        alt.Chart(df_plot)
        .mark_image(width=24, height=24, yOffset=-15)
        .encode(
            x=alt.X("selecao:N", sort="-y"),
            y=alt.Y("Chances de Título (%):Q"),
            url="Ícone:N",
            tooltip=["selecao", "Chances de Título (%)"],
        )
    )

    chart = (bars + images).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### 📊 Raio-X por Fase do Torneio")

    def format_pct(x):
        return f"{x:.1%}" if isinstance(x, float) else x

    df_display = df_probs.copy()

    for col in [
        "prob_grupo",
        "prob_oitavas",
        "prob_quartas",
        "prob_semi",
        "prob_final",
        "prob_campea",
    ]:
        df_display[col] = df_display[col].apply(format_pct)

    # Insert SVG icons as a column
    df_display.insert(0, "Ícone", df_display["selecao"].apply(obter_svg_data_uri))
    df_display.columns = [
        "Ícone",
        "Seleção",
        "Grupos (R32)",
        "Oitavas",
        "Quartas",
        "Semifinal",
        "Final",
        "Campeã",
    ]

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={"Ícone": st.column_config.ImageColumn("Ícone", width="small")},
    )
# ==========================================
# PÁGINA 3: EXPLORADOR DE PARTIDAS 1v1
# ==========================================
elif page == "Explorador de partidas":
    st.title("🔬 Explorador de xG (Expected Goals)")

    st.markdown(
        "Escolha duas equipes para invocar o cérebro preditivo de Poisson puro."
    )

    todas = sorted(list(df_grupos["nation"].unique()))

    col1, col2 = st.columns(2)

    with col1:
        time1 = st.selectbox(
            "Mandante (Casa)",
            options=todas,
            index=todas.index("Brazil") if "Brazil" in todas else 0,
        )

    with col2:
        time2 = st.selectbox(
            "Visitante (Fora)",
            options=todas,
            index=todas.index("France") if "France" in todas else 1,
        )

    # Mostrar as bandeiras SVG grandes antes do botão
    st.markdown(
        f"<h3 style='text-align: center; padding: 20px 0;'>{com_bandeira_html(time1)} &nbsp; ⚔️ &nbsp; {com_bandeira_html(time2)}</h3>",
        unsafe_allow_html=True,
    )

    eh_neutro = st.checkbox("🏟️ Campo Neutro (Retira viés de casa/fora)")

    if st.button("🔮 Calcular Estimativa"):
        resultado = prever_jogo(time1, time2, neutro=eh_neutro)

        st.markdown("---")
        st.markdown(
            f"### {com_bandeira_html(time1)} ⚔️ {com_bandeira_html(time2)}",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        c1.metric(
            f"xG (Gols Esperados) {time1}",
            f"{resultado['gols_esperados_casa']:.2f}",
        )

        c2.metric(
            f"xG (Gols Esperados) {time2}",
            f"{resultado['gols_esperados_visitante']:.2f}",
        )

        st.markdown("#### Chance de Resultado:")

        p_v = resultado["prob_vitoria"]
        p_e = resultado["prob_empate"]
        p_d = resultado["prob_derrota"]

        st.progress(p_v, text=f"Vitória {time1} ({p_v:.1%})")
        st.progress(p_e, text=f"Empate ({p_e:.1%})")
        st.progress(p_d, text=f"Vitória {time2} ({p_d:.1%})")

# # ==========================================
# PÁGINA 4: RANKING DOS PALPITES
# ==========================================
elif page == "Ranking dos Palpites":
    st.title("🏆 Ranking Oficial da Copa")
    st.markdown(
        "Confira a pontuação dos participantes do bolão com base nos resultados reais da Copa."
    )

    from palpites import carregar_palpites
    from core.tournament_state import get_current_real_results
    from core.scoring import process_ranking
    from live_results import fetch_all_fixtures
    from results_repository import upsert_fixtures, get_last_sync_time, update_sync_time
    import datetime

    # CSS Customizado foi movido para a função aplicar_tema()

    col1, col2 = st.columns([3, 1])

    with col1:
        sync_key = "fixtures_all_worldcup"
        last_sync = get_last_sync_time(sync_key)

        if last_sync:
            if last_sync.tzinfo is None:
                last_sync = last_sync.replace(tzinfo=datetime.timezone.utc)

            st.caption(
                f"Última sincronização: {last_sync.strftime('%d/%m/%Y %H:%M:%S')}"
            )
        else:
            st.caption("Última sincronização: Nunca")

    with col2:
        if st.button("🔄 Buscar resultados agora"):
            now = datetime.datetime.now(datetime.timezone.utc)

            if last_sync and (now - last_sync).total_seconds() < 900:
                st.warning("⚠️ Aguarde 15 minutos entre atualizações.")
            else:
                with st.spinner("Buscando resultados na API World Cup..."):
                    try:
                        fixtures = fetch_all_fixtures()
                        new_finished = upsert_fixtures(fixtures)
                        update_sync_time(sync_key)

                        # Limpa cache para garantir que o ranking use os dados novos
                        st.cache_data.clear()

                        if new_finished:
                            st.success(
                                "Novos resultados finalizados encontrados! Atualizando ranking..."
                            )
                        else:
                            st.info(
                                "Sincronização concluída. Nenhum novo jogo finalizado."
                            )

                    except Exception as e:
                        st.error(f"Erro ao buscar API: {e}")

    df_palpites = carregar_palpites()
    real_results = get_current_real_results()
    df_ranking = process_ranking(df_palpites, real_results)

    if not df_ranking.empty:
        total_participantes = len(df_ranking)
        lider = df_ranking.iloc[0]
        pontos_lider = lider.get("total_score", 0)
        media_pontos = df_ranking["total_score"].mean()

        # === SEÇÃO 1: MÉTRICAS ===
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Participantes", total_participantes)
        c2.metric("Líder", f"{pontos_lider} pts")
        c3.metric("Média", f"{media_pontos:.1f} pts")
        c4.metric("Última Sync", last_sync.strftime("%H:%M") if last_sync else "--")

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # RESUMO AUTOMÁTICO
        # ==========================================
        st.markdown("---")

        lider = df_ranking.iloc[0]

        nome_lider = lider.get("user_name", "Participante")
        pontos_lider = lider.get("total_score", 0)
        palpites_corretos = lider.get("palpites_corretos", 0)
        score_grupos = lider.get("score_grupos", 0)
        score_mata_mata = lider.get("score_mata_mata", 0)
        score_finais = lider.get("score_finais", 0)

        total_participantes = len(df_ranking)
        segundo_html = ""

        if total_participantes >= 2:
            segundo = df_ranking.iloc[1]
            nome_segundo = segundo.get("user_name", "Segundo colocado")
            pontos_segundo = segundo.get("total_score", 0)
            diferenca = pontos_lider - pontos_segundo

            if diferenca == 0:
                segundo_html = dedent(
                    f"""
                    <p class="summary-second warning">
                        ⚠️ <b>Empate no topo!</b> <b>{nome_segundo}</b> também tem 
                        <b>{pontos_segundo} pontos</b>.
                    </p>
                    """
                ).strip()
            else:
                segundo_html = dedent(
                    f"""
                    <p class="summary-second">
                        🥈 <b>{nome_segundo}</b> vem logo atrás com 
                        <b>{pontos_segundo} pontos</b>, diferença de 
                        <b>{diferenca} ponto(s)</b>.
                    </p>
                    """
                ).strip()

        html_summary = dedent(
            f"""
            <div class="summary-card">
                <h3>📊 Resumo Automático</h3>

                <p class="summary-main">
                    🏆 <b>{nome_lider}</b> lidera com 
                    <b>{pontos_lider} pontos</b>. 
                    Acumula <b>{palpites_corretos} palpites corretos</b>.
                </p>

                <div class="summary-grid">
                    <div>
                        <span>Grupos</span>
                        <strong>{score_grupos}</strong>
                    </div>
                    <div>
                        <span>Mata-mata</span>
                        <strong>{score_mata_mata}</strong>
                    </div>
                    <div>
                        <span>Finais</span>
                        <strong>{score_finais}</strong>
                    </div>
                </div>

                {segundo_html}
            </div>
            """
        ).strip()

        st.markdown(html_summary.replace("\n", ""), unsafe_allow_html=True)

        # === SEÇÃO 3: CARDS DE PARTICIPANTES ===
        def render_ranking_card(row, index, destaque_cor="#6366f1", medalha=""):
            pos = int(row.get("posicao", index + 1))
            nome = row.get("user_name", "Anônimo")
            pontos = row.get("total_score", 0)
            acertos = row.get("palpites_corretos", 0)
            grupos = row.get("score_grupos", 0)
            mata_mata = row.get("score_mata_mata", 0)
            finais = row.get("score_finais", 0)

            titulo = (
                f"#{pos} {medalha} &mdash; {nome}"
                if medalha
                else f"#{pos} &mdash; {nome}"
            )

            card_html = dedent(
                f"""
                <div class="ranking-card" style="border-left-color: {destaque_cor};">
                    <div class="flex-row">
                        <div class="other-rank-name">
                            {titulo}
                        </div>
                        <div style="font-size: 20px; font-weight: bold; color: {destaque_cor};">
                            {pontos} pts
                        </div>
                    </div>

                    <div class="ranking-meta">
                        ✅ Acertos: {acertos} &nbsp;|&nbsp;
                        Grupos: {grupos} &nbsp;|&nbsp;
                        Mata-mata: {mata_mata} &nbsp;|&nbsp;
                        Finais: {finais}
                    </div>
                </div>
                """
            ).strip()

            st.markdown(card_html.replace("\n", ""), unsafe_allow_html=True)

        st.markdown("<br><h3>🏆 Top 3</h3>", unsafe_allow_html=True)

        top_colors = {
            1: ("#FFDE21", "🥇"),
            2: ("#D1D5DB", "🥈"),
            3: ("#CD7F32", "🥉"),
        }

        for i in range(min(3, len(df_ranking))):
            row = df_ranking.iloc[i]
            pos = int(row.get("posicao", i + 1))
            cor, medalha = top_colors.get(pos, ("#6366f1", ""))
            render_ranking_card(row, index=i, destaque_cor=cor, medalha=medalha)

        if len(df_ranking) > 3:
            st.markdown("### 🏃 Demais Participantes")

            for i in range(3, len(df_ranking)):
                render_ranking_card(
                    df_ranking.iloc[i], index=i, destaque_cor="#6366f1", medalha=""
                )

        # === TABELA COMPLETA OPCIONAL ===
        with st.expander("📋 Ver tabela completa"):
            colunas_ranking = [
                "posicao",
                "user_name",
                "total_score",
                "palpites_corretos",
                "score_grupos",
                "score_mata_mata",
                "score_finais",
            ]

            colunas_existentes = [
                coluna for coluna in colunas_ranking if coluna in df_ranking.columns
            ]

            st.dataframe(
                df_ranking[colunas_existentes],
                use_container_width=True,
                hide_index=True,
            )

        # === SEÇÃO 4: VISUALIZADOR DE PALPITES ===
        try:
            from palpites_viewer import render_user_predictions

            render_user_predictions(df_palpites)
        except Exception as e:
            st.error(f"Erro ao carregar visualizador de palpites: {e}")

    else:
        st.warning(
            "Nenhum palpite foi registrado ainda ou não há resultados processados."
        )

# ==========================================
# PÁGINA 5: ESTATÍSTICAS EM TEMPO REAL
# ==========================================
elif page == "Estatísticas em tempo real":
    st.title("📈 Estatísticas em tempo real")

    st.markdown(
        "⚠️ **Aviso:** Estas são projeções dinâmicas estimadas com base no desempenho "
        "atual das seleções e nos resultados já sincronizados. "
        "**Não são probabilidades oficiais consolidadas**."
    )

    from live_results import fetch_all_fixtures
    from results_repository import (
        upsert_fixtures,
        get_last_sync_time,
        update_sync_time,
        get_all_real_results,
    )
    import datetime
    from core.live_podium_stats import calcular_estatisticas_podio

    # Usa a mesma chave da página de Ranking, pois agora sincronizamos todos os jogos
    sync_key = "fixtures_all_worldcup"

    col1, col2 = st.columns([3, 1])

    with col1:
        last_sync = get_last_sync_time(sync_key)

        if last_sync:
            if last_sync.tzinfo is None:
                last_sync = last_sync.replace(tzinfo=datetime.timezone.utc)

            st.caption(
                f"Última sincronização: {last_sync.strftime('%d/%m/%Y %H:%M:%S')}"
            )
        else:
            st.caption("Última sincronização: Nunca")

    with col2:
        if st.button("🔄 Sincronizar todos os jogos"):
            now = datetime.datetime.now(datetime.timezone.utc)

            if last_sync and (now - last_sync).total_seconds() < 900:
                st.warning("⚠️ Aguarde 15 minutos entre atualizações.")
            else:
                with st.spinner("Sincronizando todos os jogos da Copa..."):
                    try:
                        fixtures = fetch_all_fixtures()
                        new_finished = upsert_fixtures(fixtures)
                        update_sync_time(sync_key)

                        # Limpa cache para garantir que gráficos e ranking usem dados novos
                        st.cache_data.clear()

                        if new_finished:
                            st.success(
                                "Novos jogos finalizados foram encontrados. "
                                "Estatísticas atualizadas!"
                            )
                        else:
                            st.info(
                                "Sincronização concluída. "
                                "Nenhum novo jogo finalizado encontrado."
                            )

                    except Exception as e:
                        st.error("Erro ao sincronizar dados da World Cup API.")
                        st.caption(f"Detalhe técnico: {e}")

    df_probs = buscar_probabilidades_completas()
    df_real = get_all_real_results()

    if df_real.empty:
        st.warning(
            "Nenhum resultado real foi encontrado em `real_results`. "
            "Clique em **Sincronizar todos os jogos** para carregar os dados da Copa."
        )

    if not df_probs.empty:
        df_dyn = calcular_estatisticas_podio(df_probs, df_real)

        # Adiciona ícones e formatação percentual
        df_dyn["Ícone"] = df_dyn["selecao"].apply(obter_svg_data_uri)
        df_dyn["% Campeão"] = df_dyn["chance_campeao"] * 100
        df_dyn["% Vice"] = df_dyn["chance_vice"] * 100
        df_dyn["% Terceiro"] = df_dyn["chance_terceiro"] * 100

        st.markdown("---")

        c_champ, c_vice, c_third = st.columns(3)

        with c_champ:
            st.subheader("🥇 Top 12 Campeão")

            df_champ = df_dyn.sort_values("chance_campeao", ascending=False).head(12)

            st.altair_chart(
                alt.Chart(df_champ)
                .mark_bar(color="#FFD700")
                .encode(
                    x=alt.X(
                        "selecao:N",
                        sort="-y",
                        title=None,
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("% Campeão:Q", title="Chance (%)"),
                    tooltip=["selecao", "% Campeão"],
                )
                .properties(height=300),
                use_container_width=True,
            )

        with c_vice:
            st.subheader("🥈 Top 12 Vice")

            df_vice = df_dyn.sort_values("chance_vice", ascending=False).head(12)

            st.altair_chart(
                alt.Chart(df_vice)
                .mark_bar(color="#C0C0C0")
                .encode(
                    x=alt.X(
                        "selecao:N",
                        sort="-y",
                        title=None,
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("% Vice:Q", title="Chance (%)"),
                    tooltip=["selecao", "% Vice"],
                )
                .properties(height=300),
                use_container_width=True,
            )

        with c_third:
            st.subheader("🥉 Top 12 Terceiro")

            df_third = df_dyn.sort_values("chance_terceiro", ascending=False).head(12)

            st.altair_chart(
                alt.Chart(df_third)
                .mark_bar(color="#CD7F32")
                .encode(
                    x=alt.X(
                        "selecao:N",
                        sort="-y",
                        title=None,
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("% Terceiro:Q", title="Chance (%)"),
                    tooltip=["selecao", "% Terceiro"],
                )
                .properties(height=300),
                use_container_width=True,
            )

        st.markdown("---")
        st.subheader("📋 Tabela Completa de Estatísticas")

        colunas_tabela = [
            "Ícone",
            "selecao",
            "fator_performance",
            "chance_campeao",
            "chance_vice",
            "chance_terceiro",
        ]

        colunas_existentes = [
            coluna for coluna in colunas_tabela if coluna in df_dyn.columns
        ]

        df_display = df_dyn[colunas_existentes].copy()

        for col in ["chance_campeao", "chance_vice", "chance_terceiro"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}")

        if "fator_performance" in df_display.columns:
            df_display["fator_performance"] = df_display["fator_performance"].apply(
                lambda x: f"{x:.2f}x"
            )

        rename_cols = {
            "Ícone": "Ícone",
            "selecao": "Seleção",
            "fator_performance": "Fator Perf.",
            "chance_campeao": "Campeão",
            "chance_vice": "Vice",
            "chance_terceiro": "Terceiro",
        }

        df_display = df_display.rename(columns=rename_cols)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ícone": st.column_config.ImageColumn("Ícone", width="small")
            },
        )

    else:
        st.info("Nenhuma probabilidade pré-computada encontrada.")
