import streamlit as st
import re

st.set_page_config(page_title="Garga - Caçador de Smurf", layout="wide")

# CSS customizado: Verde para match e Azul para sem match
st.markdown("""
    <style>
    .match-box {
        background-color: rgba(20, 80, 40, 0.6);
        border: 1px solid #28a745;
        padding: 10px;
        border-radius: 5px;
        color: #d4edda;
        margin-bottom: 8px;
        font-family: monospace;
    }
    .nomatch-box {
        background-color: rgba(25, 50, 100, 0.6);
        border: 1px solid #007bff;
        padding: 10px;
        border-radius: 5px;
        color: #d1ecf1;
        margin-bottom: 8px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

def buscar_nome_gc(gc_id):
    db_mock = {"12345": "Celso_W", "67890": "Nathali_G"}
    return db_mock.get(gc_id, "Usuário Desconhecido")

def parse_data(text):
    keys = ["HDD", "MAC", "MODEM MAC", "WINDOWS", "TPM EK SHA256", "RAM", "MOTHERBOARD", "MONITOR", "SYSTEM UUID", "ANTI-SPOOFER"]
    found = {k: [] for k in keys}
    
    for k in keys:
        alt_k = k[1:] if k == "WINDOWS" else k
        pattern = rf"(?:{k}|{alt_k})\s*[:]?\s*(.*?)(?={'|'.join(keys)}|\d{{2}}/\d{{2}}/\d{{4}}|$)"
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        cleaned = []
        for m in matches:
            # Pega a primeira linha ou o primeiro bloco limpo que pareça um hash/ID
            lines = m.strip().split('\n')
            if lines and lines[0].strip():
                val = lines[0].strip()
                # Remove datas ou lixo que venha grudado no final
                val = re.split(r'\s+\d{2}/\d{2}/\d{4}', val)[0].strip()
                if val:
                    cleaned.append(val)
        found[k] = cleaned

    # Fallback inteligente: se não achou nada em WINDOWS mas o texto contém hashes compridos, tenta capturar
    if not found["WINDOWS"]:
        # Busca padrões longos que parecem IDs de hardware do GC
        potential_windows = re.findall(r'([0-9a-f]{20,}[g0-9a-f]*)', text, re.IGNORECASE)
        if potential_windows:
            found["WINDOWS"] = list(set(potential_windows))

    return found

if 'contas' not in st.session_state:
    st.session_state.contas = [{}, {}]

st.title("🛡️ Garga: Assistente Caçador de Smurf")

# Gerenciamento das caixas de input lado a lado
cols = st.columns(len(st.session_state.contas))
for i, col in enumerate(cols):
    with col:
        if len(st.session_state.contas) > 2:
            if st.button(f"❌ Excluir {i+1}", key=f"del_{i}"):
                st.session_state.contas.pop(i)
                st.rerun()
        
        gc_id = st.text_input(f"GC ID {i+1}", key=f"gc_{i}")
        nome = buscar_nome_gc(gc_id) if gc_id else f"Jogador {i+1}"
        st.markdown(f"**👤 {nome}**")
        data = st.text_area(f"Dados Brutos {i+1}", key=f"data_{i}", height=150)
        st.session_state.contas[i] = {"id": gc_id, "nome": nome, "dados": parse_data(data)}

if st.button("➕ Adicionar mais 1"):
    st.session_state.contas.append({})
    st.rerun()

st.divider()

if st.button("🔍 ANALISAR"):
    st.subheader("📊 Resultado da Análise de Windows IDs")
    
    # Encontrar quais Windows IDs aparecem em contas DIFERENTES
    windows_por_conta = [set(c['dados']['WINDOWS']) for c in st.session_state.contas]
    
    shared_windows = set()
    for i in range(len(windows_por_conta)):
        for j in range(i + 1, len(windows_por_conta)):
            shared_windows.update(windows_por_conta[i] & windows_por_conta[j])
    
    if shared_windows:
        st.success("🟢 **MATCH ENCONTRADO!** Há Windows ID(s) compartilhado(s) entre as contas.")
    else:
        st.info("ℹ️ **NENHUM MATCH.** Nenhum Windows ID compartilhado entre as contas informadas.")

    st.markdown("---")
    st.markdown("### 📋 Visão Geral por Jogador:")
    
    # Exibir por coluna organizando os Windows compartilhados no topo
    res_cols = st.columns(len(st.session_state.contas))
    for i, col in enumerate(res_cols):
        conta = st.session_state.contas[i]
        with col:
            st.markdown(f"### {conta.get('nome', 'Desconhecido')}")
            st.caption(f"ID: {conta.get('id', '-')}")
            st.markdown("---")
            
            raw_windows = conta['dados']['WINDOWS']
            if not raw_windows:
                st.write("_Nenhum Windows encontrado._")
                continue
                
            # Ordenar: Colocar os compartilhados primeiro
            sorted_windows = sorted(raw_windows, key=lambda w: 0 if w in shared_windows else 1)
            
            for w in sorted_windows:
                if w in shared_windows:
                    st.markdown(f'<div class="match-box">🟢 WINDOWS: {w}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="nomatch-box">🔵 WINDOWS: {w}</div>', unsafe_allow_html=True)