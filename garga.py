import streamlit as st
import re

st.set_page_config(page_title="Garga - Caçador de Smurf", layout="wide")

st.title("🛡️ Garga: Assistente Caçador de Smurf")
st.write("Insira os dados das contas para comparar HWIDs.")

# Lista de chaves que o sistema deve procurar
keys = ["HDD", "MAC", "MODEM MAC", "WINDOWS", "TPM EK SHA256", "RAM", "MOTHERBOARD", "MONITOR", "SYSTEM UUID", "ANTI-SPOOFER"]

def parse_data(text):
    """Extrai os dados do texto bagunçado usando Regex"""
    found = {k: [] for k in keys}
    for k in keys:
        # Regex busca a chave, pega tudo até a próxima data ou próxima chave conhecida
        pattern = rf"{k}(.*?)(?={'|'.join(keys)}|\d{{2}}/\d{{2}}/\d{{4}})"
        matches = re.findall(pattern, text, re.DOTALL)
        found[k] = [m.strip() for m in matches if m.strip()]
    return found

# Gerenciamento de contas via Session State
if 'contas' not in st.session_state:
    st.session_state.contas = [{}, {}] # Começa com 2

# Interface Dinâmica
cols = st.columns(len(st.session_state.contas))
for i, col in enumerate(cols):
    with col:
        st.subheader(f"Conta {i+1}")
        gc_id = st.text_input(f"GC ID {i+1}", key=f"gc_{i}")
        data = st.text_area(f"Dados Brutos {i+1}", key=f"data_{i}", height=200)
        st.session_state.contas[i] = {"id": gc_id, "dados": parse_data(data)}

if st.button("Adicionar mais 1"):
    st.session_state.contas.append({})
    st.rerun()

if st.button("ANALISAR"):
    st.divider()
    # Lógica de Comparação
    for i in range(len(st.session_state.contas)):
        for j in range(i + 1, len(st.session_state.contas)):
            c1, c2 = st.session_state.contas[i], st.session_state.contas[j]
            
            # Comparação de Windows
            match = set(c1['dados']['WINDOWS']) & set(c2['dados']['WINDOWS'])
            
            color = "green" if match else "red"
            st.markdown(f"### Comparação: {c1['id']} vs {c2['id']}")
            st.markdown(f":{color}[Status: {'MATCH ENCONTRADO!' if match else 'Sem match de Windows'}]")
            
            if match:
                st.info(f"Windows compartilhados: {', '.join(match)}")