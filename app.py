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


engine, df_jogos, df_grupos, df_mata = injetar_dependencias()


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("⚽ Copa 2026 (AI)")

page = st.sidebar.radio(
    "Navegação",
    [
        "Probabilidades Pré-computadas",
        "Simulação ao vivo",
        "Explorador de partidas",
    ],
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
# PÁGINA 2: SIMULADOR AO VIVO
# ==========================================
elif page == "Simulação ao vivo":
    st.title("🎲 Multiverso da Copa (Ao Vivo)")

    st.markdown(
        "A cada clique, a Inteligência Artificial joga os dados matemáticos "
        "do Poisson gerando uma nova linha temporal exclusiva da Copa inteira."
    )

    if st.button("▶ Rodar Simulação Interativa!", type="primary"):
        np.random.seed(None)

        with st.spinner("Gerando universos alternativos..."):
            resultado = simular_torneio_detalhado(df_jogos, df_grupos, df_mata)
            st.session_state["resultado_live"] = resultado

    if "resultado_live" in st.session_state:
        res = st.session_state["resultado_live"]
        podio = res["podio"]

        st.markdown(
            f'<div style="padding: 1rem; border-radius: 0.5rem; background-color: rgba(40, 167, 69, 0.2); margin-bottom: 1rem;">'
            f'<h3 style="margin: 0; color: #28a745;">🥇 <b>CAMPEÃO:</b> {com_bandeira_html(podio.get("campeao", "Unknown"))}</h3>'
            f"</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                f'<div style="padding: 0.75rem; border-radius: 0.5rem; background-color: rgba(23, 162, 184, 0.2);">'
                f'<span style="color: #17a2b8; font-weight: bold;">🥈 Vice:</span> {com_bandeira_html(podio.get("vice", "Unknown"))}'
                f"</div>",
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f'<div style="padding: 0.75rem; border-radius: 0.5rem; background-color: rgba(255, 193, 7, 0.2);">'
                f'<span style="color: #ffc107; font-weight: bold;">🥉 Terceiro:</span> {com_bandeira_html(podio.get("terceiro", "Unknown"))}'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.subheader("⚔️ Caminho do Mata-Mata")

        mata_data = res["mata_mata"]

        etapas = [
            ("Final", "FINAL"),
            ("Disputa 3º", "3RD_PLACE"),
            ("Semifinais", "SF"),
            ("Quartas", "QF"),
            ("Oitavas", "R16"),
            ("32-Avos (R32)", "R32"),
        ]

        for titulo, chave in etapas:
            jogos_fase = mata_data.get(chave, [])

            if not jogos_fase:
                continue

            with st.expander(
                f"{titulo} ({len(jogos_fase)} jogos)",
                expanded=(chave == "FINAL"),
            ):
                for j in jogos_fase:
                    tc = com_bandeira_html(j["time_casa"])
                    tv = com_bandeira_html(j["time_visitante"])
                    gc = j["gols_casa"]
                    gv = j["gols_visitante"]

                    texto_placar = f"{tc} <b>{gc} x {gv}</b> {tv}"

                    if j["penaltis"]:
                        pc = j["pen_casa"]
                        pv = j["pen_visitante"]
                        texto_placar += f" <i>(Pênaltis: {pc}-{pv})</i>"

                    st.markdown(texto_placar, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Classificação dos Grupos")

        df_g = res["grupos"].copy()

        # Add Icon column
        df_g.insert(0, "Ícone", df_g["selecao"].apply(obter_svg_data_uri))

        cols_pt = [
            "grupo",
            "posicao",
            "Ícone",
            "selecao",
            "jogos",
            "vitorias",
            "empates",
            "derrotas",
            "gols_pro",
            "gols_contra",
            "saldo_gols",
            "pontos",
        ]

        df_g = df_g[cols_pt]

        for g, df_grupo in df_g.groupby("grupo"):
            with st.expander(f"Grupo {g}"):
                st.dataframe(
                    df_grupo.drop("grupo", axis=1).style.highlight_max(
                        subset=["pontos"]
                    ),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Ícone": st.column_config.ImageColumn("Ícone", width="small")
                    },
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
