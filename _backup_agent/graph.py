import os
from typing import TypedDict, List, Dict, Any, Literal
import pandas as pd
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Imports locais do Core e DB
from core.scoring import process_ranking
from core.tournament_state import get_current_real_results, calculate_max_potential
from palpites import carregar_palpites
from db import get_secret_or_env


# ==========================================
# 1. DEFINIÇÃO DO ESTADO DO GRAFO
# ==========================================
class AgentState(TypedDict, total=False):
    """
    O estado que transita entre os nós do LangGraph.
    """

    user_query: str  # Pergunta/Input do Streamlit
    messages: List[Any]  # Histórico de mensagens do chat
    real_results: Dict[str, Any]  # Dados dos resultados reais até o momento
    ranking_data: List[Dict[str, Any]]  # Ranking atual (top 5 pra caber no context)
    leader_name: str  # Nome do líder atual
    ai_status: str  # Se a IA está ganhando, perdendo ou competitiva
    persona: str  # Persona escolhida dinamicamente
    final_response: str  # Resposta final em markdown gerada pelo LLM


# ==========================================
# 2. DEFINIÇÃO DOS NÓS (NODES)
# ==========================================
def gather_data_node(state: AgentState) -> AgentState:
    """
    Nó responsável por chamar as "tools" para buscar os resultados reais
    e a base de palpites do banco de dados (Read-Only).
    """
    # Tool: get_real_results
    real_results = get_current_real_results()

    # Tool: get_existing_predictions
    df_palpites = carregar_palpites()

    # Processa o ranking com os dados core
    df_ranking = process_ranking(df_palpites, real_results)

    ranking_dict = []
    leader = "Indefinido"
    if not df_ranking.empty:
        # Pega o Top 5 para não estourar o limite de tokens do prompt
        ranking_dict = df_ranking.head(5).to_dict(orient="records")
        leader = df_ranking.iloc[0]["user_name"]

    return {
        "real_results": real_results,
        "ranking_data": ranking_dict,
        "leader_name": leader,
    }


def persona_router_node(
    state: AgentState,
) -> Literal["narrador_node", "palpiteiro_node"]:
    """
    Condicional (Edge) que define qual "Modo" o agente deve assumir.
    Por enquanto a lógica é simples: se a IA (a ser implementado no ranking) estiver
    perdendo muito ou houver uma virada dramática, ativa 'palpiteiro'.
    """
    # Lógica hardcoded de exemplo.
    # TODO: Refinar para comparar pontuação da IA x líder real.
    leader = state.get("leader_name", "")

    # Apenas um exemplo de provocação se alguem específico liderar.
    if leader == "Daniel" or leader == "Vitor Mello":
        return "palpiteiro_node"

    return "narrador_node"


def _generate_response(state: AgentState, system_prompt: str) -> AgentState:
    """Função utilitária para chamar o LLM."""
    api_key = get_secret_or_env("GEMINI_API_KEY")

    llm = ChatGoogleGenerativeAI(
        model="Gemini 2.5 Flash", google_api_key=api_key, temperature=0.7
    )

    # Prepara o contexto com os dados matemáticos do Core
    context = f"""
    ESTADO ATUAL DO TORNEIO (Resultados Reais):
    {state.get('real_results')}
    
    RANKING ATUAL (TOP 5):
    {state.get('ranking_data')}
    
    PERGUNTA DO USUÁRIO NO DASHBOARD:
    {state.get('user_query')}
    """

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=context)]

    response = llm.invoke(messages)

    return {"final_response": str(response.content)}


def narrador_node(state: AgentState) -> AgentState:
    """Nó que gera uma resposta formal, focada em análise estatística."""
    prompt = """
    Você é o Analista Oficial da Copa do Mundo 2026. 
    Sua função é explicar o ranking atual dos usuários baseando-se estritamente nos dados fornecidos.
    Seja analítico, formal e aponte matematicamente quem acertou grupos ou mata-mata.
    Não invente resultados reais que não estejam no contexto.
    """
    return _generate_response(state, prompt)


def palpiteiro_node(state: AgentState) -> AgentState:
    """Nó que gera uma resposta provocativa e divertida."""
    prompt = """
    Você é o 'Palpiteiro', um comentarista de futebol bem humorado, provocativo e ligeiramente ácido sobre a Copa do Mundo 2026.
    Sua função é comentar o ranking dos usuários. Brinque com o líder, diga que foi 'sorte' ou comemore ironicamente.
    Se a inteligência artificial estiver perdendo para humanos, dê desculpas furadas matemáticas.
    Mantenha o tom de mesa redonda de futebol brasileiro.
    Não invente resultados que não estejam no contexto.
    """
    return _generate_response(state, prompt)


# ==========================================
# 3. CONSTRUÇÃO DO GRAFO LANGGRAPH
# ==========================================
def build_agent_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Adicionando os nós
    workflow.add_node("gather_data", gather_data_node)
    workflow.add_node("narrador_node", narrador_node)
    workflow.add_node("palpiteiro_node", palpiteiro_node)

    # Definindo as arestas (Edges)
    workflow.set_entry_point("gather_data")

    # Aresta condicional após coletar os dados
    workflow.add_conditional_edges(
        "gather_data",
        persona_router_node,
        {"narrador_node": "narrador_node", "palpiteiro_node": "palpiteiro_node"},
    )

    # Finalizando o grafo
    workflow.add_edge("narrador_node", END)
    workflow.add_edge("palpiteiro_node", END)

    return workflow.compile()


# Função principal exportada para o Streamlit
def ask_agent(user_query: str) -> str:
    from typing import cast

    app = build_agent_graph()
    initial_state = {"user_query": user_query, "messages": []}

    result = cast(Any, app).invoke(initial_state)
    return str(result.get("final_response", ""))
