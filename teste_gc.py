from playwright.sync_api import sync_playwright

def raspar_perfil_gc_com_brave(gc_id):
    url = f"https://gamersclub.com.br/player/{gc_id}"
    
    with sync_playwright() as p:
        # Lança o navegador apontando para o executável do Brave instalado no Windows
        try:
            browser = p.chromium.launch(
                executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                headless=False  # False para você acompanhar a automação na tela
            )
        except Exception as e:
            print("Caminho padrão do Brave não encontrado. Tentando pelo executável alternativo (x86)...")
            browser = p.chromium.launch(
                executable_path=r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                headless=False
            )
            
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Acessando o perfil no Brave: {url}")
        page.goto(url)
        
        try:
            print("Aguardando carregamento da página...")
            page.wait_for_selector("text=Conta GC", timeout=15000)
        except Exception:
            print("Aguardando login ou carregamento...")
            page.wait_for_timeout(10000)
        
        conteudo_pagina = page.inner_text("body")
        
        print("\n--- DADOS CAPTURADOS PELO BRAVE ---")
        print(conteudo_pagina[:1000])
        
        browser.close()

if __name__ == "__main__":
    id_alvo = "1328862"
    raspar_perfil_gc_com_brave(id_alvo)