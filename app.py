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


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("⚽ Copa 2026 (AI)")

page = st.sidebar.radio(
    "Navegação",
    [
        "Probabilidades Pré-computadas",
        "Explorador de partidas",
        "Ranking dos Palpites",
        "Estatísticas em tempo real",
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
    from live_results import fetch_daily_fixtures
    from results_repository import upsert_fixtures, get_last_sync_time, update_sync_time
    import datetime

    col1, col2 = st.columns([3, 1])

    with col1:
        sync_key = "fixtures_today"
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
                with st.spinner("Buscando resultados na API-Football..."):
                    try:
                        fixtures = fetch_daily_fixtures()
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

        # ==========================================
        # RESUMO AUTOMÁTICO SEM LLM
        # ==========================================
        st.markdown("---")
        st.subheader("📊 Resumo Automático")

        lider = df_ranking.iloc[0]

        nome_lider = lider.get("user_name", "Participante")
        pontos_lider = lider.get("total_score", 0)
        palpites_corretos = lider.get("palpites_corretos", 0)
        score_grupos = lider.get("score_grupos", 0)
        score_mata_mata = lider.get("score_mata_mata", 0)
        score_finais = lider.get("score_finais", 0)

        total_participantes = len(df_ranking)

        st.info(
            f"🏆 **{nome_lider}** está liderando o ranking com "
            f"**{pontos_lider} pontos**. "
            f"Até agora, o líder soma **{palpites_corretos} palpites corretos**, "
            f"com **{score_grupos} pontos em grupos**, "
            f"**{score_mata_mata} pontos no mata-mata** e "
            f"**{score_finais} pontos em finais/terceiro lugar**."
        )

        st.caption(
            f"O ranking possui {total_participantes} participante(s) e é calculado "
            "automaticamente com base nos resultados reais já sincronizados."
        )

        if total_participantes >= 2:
            segundo = df_ranking.iloc[1]
            nome_segundo = segundo.get("user_name", "Segundo colocado")
            pontos_segundo = segundo.get("total_score", 0)
            diferenca = pontos_lider - pontos_segundo

            st.warning(
                f"🥈 **{nome_segundo}** está em segundo lugar com "
                f"**{pontos_segundo} pontos**, a **{diferenca} ponto(s)** do líder."
            )

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
        "⚠️ **Aviso:** Estas são projeções dinâmicas estimadas baseadas no desempenho atual da vida real. **Não são probabilidades oficiais consolidadas** (que requerem milhares de simulações com Monte Carlo)."
    )

    from live_results import fetch_daily_fixtures
    from results_repository import (
        upsert_fixtures,
        get_last_sync_time,
        update_sync_time,
        get_all_real_results,
    )
    import datetime
    from core.live_podium_stats import calcular_estatisticas_podio

    col1, col2 = st.columns([3, 1])

    with col1:
        sync_key = "fixtures_today_stats"
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
        if st.button("🔄 Sincronizar dados da API"):
            now = datetime.datetime.now(datetime.timezone.utc)
            if last_sync and (now - last_sync).total_seconds() < 900:
                st.warning("⚠️ Aguarde 15 minutos entre atualizações.")
            else:
                with st.spinner("Buscando resultados da API..."):
                    try:
                        fixtures = fetch_daily_fixtures()
                        upsert_fixtures(fixtures)
                        update_sync_time(sync_key)
                        st.cache_data.clear()
                        st.success("Dados atualizados!")
                    except Exception as e:
                        st.error(f"Erro ao buscar API: {e}")

    df_probs = buscar_probabilidades_completas()
    df_real = get_all_real_results()

    if not df_probs.empty:
        df_dyn = calcular_estatisticas_podio(df_probs, df_real)

        # Adiciona Ícones e Formatação Percentual
        df_dyn["Ícone"] = df_dyn["selecao"].apply(obter_svg_data_uri)
        df_dyn["% Campeão"] = df_dyn["chance_campeao"] * 100
        df_dyn["% Vice"] = df_dyn["chance_vice"] * 100
        df_dyn["% Terceiro"] = df_dyn["chance_terceiro"] * 100

        # Gráficos de barras Altair
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

        # Tabela Completa
        st.markdown("---")
        st.subheader("📋 Tabela Completa de Estatísticas")

        # Formatando para exibição
        df_display = df_dyn[
            [
                "Ícone",
                "selecao",
                "pontos",
                "jogos",
                "gols_pro",
                "gols_contra",
                "saldo_gols",
                "fator_performance",
                "chance_campeao",
                "chance_vice",
                "chance_terceiro",
            ]
        ].copy()

        for col in ["chance_campeao", "chance_vice", "chance_terceiro"]:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}")

        df_display["fator_performance"] = df_display["fator_performance"].apply(
            lambda x: f"{x:.2f}x"
        )

        # Tradução de colunas
        df_display.columns = [
            "Ícone",
            "Seleção",
            "Pts",
            "Jogos",
            "GP",
            "GC",
            "SG",
            "Fator Perf.",
            "Campeão",
            "Vice",
            "Terceiro",
        ]

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
