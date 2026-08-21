import customtkinter as ctk
import os
import threading
from playwright.sync_api import sync_playwright

# Configuração da Janela Principal
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GargaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛡️ Garga: Caçador de Smurfs")
        self.geometry("900x700")
        
        # Título
        self.lbl_title = ctk.CTkLabel(self, text="Análise de HWID (Foco: Windows)", font=("Arial", 20, "bold"))
        self.lbl_title.pack(pady=10)

        # Entrada de IDs
        self.lbl_instrucao = ctk.CTkLabel(self, text="Cole os Steam IDs abaixo (um por linha):")
        self.lbl_instrucao.pack(pady=5)
        
        self.txt_ids = ctk.CTkTextbox(self, height=100, width=400)
        self.txt_ids.pack(pady=5)

        # Botão de Ação
        self.btn_analisar = ctk.CTkButton(self, text="INICIAR VARREDURA", command=self.iniciar_thread, fg_color="#8B0000", hover_color="#5C0000")
        self.btn_analisar.pack(pady=15)

        # Área de Resultados (Scrollable)
        self.scroll_resultados = ctk.CTkScrollableFrame(self, width=850, height=400)
        self.scroll_resultados.pack(pady=10, fill="both", expand=True)

    def iniciar_thread(self):
        self.btn_analisar.configure(text="Varrendo... Aguarde!", state="disabled")
        # Limpa resultados anteriores
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
            
        ids_brutos = self.txt_ids.get("1.0", "end").strip().split('\n')
        steam_ids = [sid.strip() for sid in ids_brutos if sid.strip()]
        
        # Roda o scraping em segundo plano para não travar a janela
        threading.Thread(target=self.executar_scraping, args=(steam_ids,), daemon=True).start()

    def executar_scraping(self, steam_ids):
        pasta_sessao = os.path.join(os.getcwd(), "PerfilGarga")
        dados_jogadores = []

        try:
            with sync_playwright() as p:
                navegador = p.chromium.launch_persistent_context(
                    user_data_dir=pasta_sessao,
                    channel="msedge",
                    headless=False,
                    no_viewport=True
                )
                
                page = navegador.pages[0]

                for steam_id in steam_ids:
                    # 1. Acessa o EMAC
                    page.goto(f"https://ac.gcsys.ws/panel/user/{steam_id}")
                    page.wait_for_timeout(2000)
                    
                    # Verifica se caiu na tela de login da Steam
                    if "steamcommunity.com/openid/login" in page.url or "Sign In" in page.inner_text("body"):
                        print("Aguardando login manual na Steam/EMAC...")
                        # Dá 60 segundos para você logar tranquilamente na primeira vez
                        try:
                            page.wait_for_url("**/panel/user/*", timeout=60000)
                        except:
                            pass
                        page.wait_for_timeout(2000)
                    
                    # Cria a estrutura do jogador
                    jogador = {"steam_id": steam_id, "windows": "Não encontrado", "gc_id": "", "nick": "-", "level": "-", "horas": "-"}
                    
                    # Pega o GC ID
                    try:
                        gc_element = page.locator("text=Conta GC:").locator("..")
                        jogador["gc_id"] = gc_element.inner_text().replace("Conta GC:", "").strip()
                    except:
                        pass
                        
                    # Pega o Windows
                    try:
                        page.get_by_text("HWID", exact=True).click()
                        page.wait_for_timeout(1000)
                        linhas_hwid = page.inner_text("body").split('\n')
                        for linha in linhas_hwid:
                            if linha.strip().startswith("WINDOWS"):
                                jogador["windows"] = linha.replace("WINDOWS", "").strip()
                                break
                    except:
                        pass
                        
                    # 2. Acessa a Gamers Club se tiver o ID
                    if jogador["gc_id"]:
                        try:
                            page.goto(f"https://gamersclub.com.br/player/{jogador['gc_id']}")
                            page.wait_for_timeout(3000) # Espera a página renderizar
                            
                            # Pegando o Nick (Normalmente o título da página é "Nick - Perfil Player | Gamers Club")
                            try:
                                titulo_pagina = page.title()
                                jogador["nick"] = titulo_pagina.split("-")[0].strip()
                            except:
                                jogador["nick"] = "Erro ao buscar"

                            # Pegando o Level
                            try:
                                # Tenta achar algo que contenha "Level" na tela
                                level_element = page.locator("text=Level").first
                                if level_element.is_visible():
                                    jogador["level"] = level_element.inner_text().strip()
                                else:
                                    jogador["level"] = "Sem Level"
                            except:
                                jogador["level"] = "Sem Level"

                            # Pegando as Horas (Com proteção caso seja privado)
                            try:
                                # Procura por algo que contenha a palavra "horas" ou "h" no card de CS2/CS:GO
                                horas_element = page.locator("text=horas").first
                                if horas_element.is_visible():
                                    jogador["horas"] = horas_element.inner_text().strip()
                                else:
                                    jogador["horas"] = "Oculto"
                            except:
                                jogador["horas"] = "Oculto"
                                
                        except Exception as e:
                            print(f"Erro na GC do ID {jogador['gc_id']}: {e}")
                    
                    dados_jogadores.append(jogador)
                    
                navegador.close()
                
        except Exception as e:
            print(f"Erro: {e}")

        # Agrupa e Atualiza a Interface
        self.atualizar_interface(dados_jogadores)

    def atualizar_interface(self, dados_jogadores):
        # Agrupa os jogadores pelo Hash do Windows
        grupos_windows = {}
        for j in dados_jogadores:
            w = j["windows"]
            if w not in grupos_windows:
                grupos_windows[w] = []
            grupos_windows[w].append(j)

        for w_hash, jogadores in grupos_windows.items():
            # Cria um "Card" para cada Windows
            frame_grupo = ctk.CTkFrame(self.scroll_resultados, fg_color="#2b2b2b", border_color="#ffcc00" if len(jogadores) > 1 else "#555555", border_width=2)
            frame_grupo.pack(pady=5, padx=10, fill="x")
            
            lbl_win = ctk.CTkLabel(frame_grupo, text=f"💻 WINDOWS: {w_hash}", font=("Arial", 12, "bold"), text_color="#00FF00" if len(jogadores) > 1 else "white")
            lbl_win.pack(anchor="w", padx=10, pady=5)
            
            for j in jogadores:
                texto_player = f"Steam: {j['steam_id']} | GC ID: {j['gc_id']} | Nick: {j['nick']} | Level: {j['level']} | Horas: {j['horas']}"
                lbl_player = ctk.CTkLabel(frame_grupo, text=f"   👤 {texto_player}", font=("Arial", 12))
                lbl_player.pack(anchor="w", padx=10, pady=2)

        self.btn_analisar.configure(text="INICIAR VARREDURA", state="normal")

if __name__ == "__main__":
    app = GargaApp()
    app.mainloop()