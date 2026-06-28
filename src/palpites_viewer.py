import json
import ast
import streamlit as st

def safe_json_loads(value):
    if value is None:
        return {}
    if isinstance(value, dict) or isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except Exception:
                pass
            return {}
    return {}

def format_val(v):
    if not v or str(v).lower() in ("null", "none", "nan", ""):
        return "A definir"
    return str(v)

def render_group_predictions(row):
    groups = safe_json_loads(row.get("group_predictions", {}))
    thirds_data = safe_json_loads(row.get("third_place_predictions", {}))
    
    with st.expander("🌍 Fase de Grupos"):
        if not groups:
            st.write("Nenhum palpite de grupos encontrado para este participante.")
            return

        thirds_dict = {}
        if isinstance(thirds_data, dict):
            selected = thirds_data.get("selected", [])
            if isinstance(selected, list):
                for item in selected:
                    if isinstance(item, list) and len(item) == 2:
                        thirds_dict[item[0]] = item[1]
        
        for group_name in sorted(groups.keys()):
            group_data = groups[group_name]
            
            first = "A definir"
            second = "A definir"
            
            if isinstance(group_data, dict):
                first = format_val(group_data.get("1st", group_data.get("1", "A definir")))
                second = format_val(group_data.get("2nd", group_data.get("2", "A definir")))
            elif isinstance(group_data, list):
                first = format_val(group_data[0]) if len(group_data) > 0 else "A definir"
                second = format_val(group_data[1]) if len(group_data) > 1 else "A definir"
                
            third = format_val(thirds_dict.get(group_name))
            
            st.markdown(f"- **Grupo {group_name.replace('Group ', '')}**: 1º {first} | 2º {second} | 3º {third}")

def render_knockout_predictions(row):
    knockout_cols = [
        'knockout_predictions', 'round_of_32_predictions', 'round_32_predictions',
        'oitavas_predictions', 'quarter_predictions', 'semifinal_predictions',
        'final_predictions', 'bracket_predictions'
    ]
    
    knockout_data = {}
    for col in knockout_cols:
        if col in row.index:
            val = safe_json_loads(row[col])
            if isinstance(val, dict):
                knockout_data.update(val)
                
    with st.expander("⚔️ Mata-mata"):
        if not knockout_data:
            st.write("Nenhum palpite de mata-mata encontrado para este participante.")
            return
            
        for match_id in sorted(knockout_data.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
            winner = format_val(knockout_data[match_id])
            st.markdown(f"- **Jogo {match_id}**: {winner}")

def render_final_predictions(row):
    champ = format_val(row.get("champion"))
    runner = format_val(row.get("runner_up"))
    third = format_val(row.get("third_place"))
    
    with st.expander("🏆 Final"):
        st.markdown(f"- **Campeão**: {champ}")
        st.markdown(f"- **Vice**: {runner}")
        st.markdown(f"- **Terceiro lugar**: {third}")

def render_user_predictions(df_palpites):
    st.markdown("---")
    st.markdown("### 🔎 Palpites dos Participantes")
    
    if df_palpites is None or df_palpites.empty:
        st.info("Nenhum palpite registrado ainda.")
        return
        
    usuarios = sorted([str(u) for u in df_palpites["user_name"].unique() if u and str(u).lower() != "nan"])
    if not usuarios:
        st.info("Nenhum usuário encontrado.")
        return
        
    selected_user = st.selectbox("Escolha um participante:", options=usuarios)
    
    if selected_user:
        row = df_palpites[df_palpites["user_name"] == selected_user].iloc[-1]
        
        render_group_predictions(row)
        render_knockout_predictions(row)
        render_final_predictions(row)
