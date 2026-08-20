import streamlit as st
import re
import os
import subprocess
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Garga - Caçador de Smurf", layout="wide")

st.markdown("""
    <style>
    .match-box { background-color: rgba(20, 80, 40, 0.6); border: 1px solid #28a745; padding: 6px; border-radius: 5px; color: #d4edda; margin-bottom: 5px; font-size: 0.8em; }
    .nomatch-box { background-color: rgba(25, 50, 100, 0.6); border: 1px solid #007bff; padding: 6px; border-radius: 5px; color: #d1ecf1; margin-bottom: 5px; font-size: 0.8em; }
    .hardware-container { height: 300px; overflow-y: auto; padding-right: 5px; }
    </style>
""", unsafe_allow_html=True)

def encontrar_brave():
    possiveis_caminhos = [
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
    ]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            return caminho
    return None

def matar_processos_brave():
    """Força o encerramento de qualquer processo travado do Brave no Windows para liberar o perfil."""
    try:
        subprocess.run(["taskkill", "/f", "/im", "brave.exe"], capture_output=True)
    except Exception:
        pass

def consultar_todas_as_contas(lista_steam_ids):
    resultados = {}
    ids_validos = [(i, sid.strip()) for i, sid in enumerate(lista_steam_ids) if sid and sid.strip()]
    
    if not ids_validos:
        return resultados

    executable_path = encontrar_brave()
    if not executable_path:
        st.error("Erro: Executável do Brave não encontrado!")
        return resultados

    # Mata processos fantasmas do Brave antes de iniciar
    matar_processos_brave()

    # Pasta de sessão dedicada para o robô salvar o login (assim você só loga uma vez)
    pasta_sessao_robo = os.path.expanduser(r'~\AppData\Local\GargaBotSession')
    os.makedirs(pasta_sessao_robo, exist_ok=True)

    try:
        with sync_playwright() as p:
            # Usa persistent_context em uma pasta separada do robô (evita conflito com o seu Brave aberto)
            context = p.chromium.launch_persistent_context(
                user_data_dir=pasta_sessao_robo,
                executable_path=executable_path,
                headless=False,
                args=["--start-maximized"]
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            for i, steam_id in ids_validos:
                nome = f"Player {steam_id[-5:]}"
                nivel = "Lvl -"
                banido = False
                hardware_detectado = {}
                
                url = f"https://ac.gcsys.ws/panel/user/{steam_id}"
                
                try:
                    page.goto(url, timeout=40000)
                    page.wait_for_timeout(2000)
                    
                    # Verifica se caiu na tela de login
                    texto_atual = page.inner_text("body")
                    if "Sign In" in texto_atual or "Login" in texto_atual or "Steam" in texto_atual and "Dashboard" not in texto_atual:
                        st.info("⚠️ Faça o login na Steam/Emaclab na janela do navegador que se abriu. O robô está aguardando...")
                        # Dá 45 segundos para você logar se for a primeira vez
                        try:
                            page.wait_for_url("**/panel/user/*", timeout=45000)
                        except:
                            pass
                    
                    page.wait_for_timeout(3000)
                    texto_body = page.inner_text("body")
                    
                    if "Banido" in texto_body or "Banned" in texto_body: 
                        banido = True
                    
                    # Clica na aba HWID
                    try:
                        aba = page.get_by_text("HWID", exact=True).first
                        if aba.is_visible():
                            aba.click()
                            page.wait_for_timeout(1500)
                    except: 
                        pass
                    
                    texto_hwid = page.inner_text("body")
                    tipos = ["HDD", "MAC", "MODEM MAC", "WINDOWS", "TPM", "RAM", "MOTHERBOARD", "MONITOR"]
                    
                    for linha in texto_hwid.split('\n'):
                        for t in tipos:
                            if linha.strip().startswith(t):
                                valor = linha.strip().replace(t, "").strip()
                                if len(valor) > 3:
                                    if t not in hardware_detectado: 
                                        hardware_detectado[t] = []
                                    if valor not in hardware_detectado[t]:
                                        hardware_detectado[t].append(valor)
                                    
                except Exception as e:
                    print(f"Erro ao ler página de {steam_id}: {e}")
                
                resultados[i] = {
                    "id": steam_id, 
                    "nome": nome, 
                    "nivel": nivel, 
                    "ban": banido, 
                    "hw": hardware_detectado
                }
                
            context.close()
            
    except Exception as e:
        st.error(f"Erro ao executar o navegador: {e}")
        
    return resultados

# --- Interface ---
if 'contas' not in st.session_state:
    st.session_state.contas = [{}, {}, {}, {}, {}]

st.title("🛡️ Garga: Caçador de Smurf")

cols = st.columns(5)
steam_inputs = []
for i, col in enumerate(cols):
    with col:
        atual = st.session_state.contas[i].get("id", "")
        val = st.text_input(f"Steam ID {i+1}", value=atual, key=f"in_{i}")
        steam_inputs.append(val)

if st.button("🔍 ANALISAR E CRUZAR HARDWARES"):
    with st.spinner("Iniciando varredura no Emaclab..."):
        dados = consultar_todas_as_contas(steam_inputs)
        
        for i in range(5):
            sid = steam_inputs[i].strip()
            if sid:
                if i in dados:
                    st.session_state.contas[i] = dados[i]
                else:
                    st.session_state.contas[i] = {
                        "id": sid, 
                        "nome": f"Player {sid[-5:]}", 
                        "nivel": "-", 
                        "ban": False, 
                        "hw": {}
                    }
            else:
                st.session_state.contas[i] = {}

# Cruzamento de Hardwares Global
mapa_hw = {}
for i, c in enumerate(st.session_state.contas):
    for tipo, vals in c.get('hw', {}).items():
        for v in vals:
            k = f"{tipo}:{v}"
            if k not in mapa_hw: 
                mapa_hw[k] = []
            mapa_hw[k].append(i)

shared = {k for k, v in mapa_hw.items() if len(set(v)) > 1}

st.divider()
st.subheader("📊 Resultado da Análise e Hardware")

res_cols = st.columns(5)
for i, col in enumerate(res_cols):
    with col:
        c = st.session_state.contas[i]
        if c and c.get('id'):
            st.markdown(f"**{c.get('nome', 'Player')}**")
            status_txt = "🔴 BANIDO" if c.get('ban') else "🟢 Ativo"
            st.write(f"Status: {status_txt}")
            
            st.markdown('<div class="hardware-container">', unsafe_allow_html=True)
            hw_dict = c.get('hw', {})
            if not hw_dict:
                st.write("_Nenhum hardware carregado._")
            else:
                for tipo, vals in hw_dict.items():
                    for v in vals:
                        is_shared = f"{tipo}:{v}" in shared
                        cls = "match-box" if is_shared else "nomatch-box"
                        st.markdown(f'<div class="{cls}"><b>{tipo}</b>: {v[:18]}...</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**Slot {i+1}**")
            st.info("Aguardando ID...")