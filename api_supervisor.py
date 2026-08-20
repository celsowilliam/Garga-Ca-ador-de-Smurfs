from fastapi import FastAPI, HTTPException
from google import genai
import json
import os
import re

app = FastAPI(title="Garga API - Supervisor Gamers Club", version="1.0")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "SUA_API_KEY_AQUI"))

@app.get("/jogador/{gc_id}")
def supervisionar_jogador(gc_id: str):
    prompt = f"""
    Acesse e pesquise na web pelo perfil da Gamers Club usando a URL ou ID: https://gamersclub.com.br/player/{gc_id}
    Encontre estritamente os seguintes dados atuais do jogador:
    1. Nick (O apelido exato dele na plataforma)
    2. Level GC (Ex: Level 10, Level 8, Lvl 5)
    3. Horas jogadas (O total de horas de CS ou na plataforma, ex: 1.500h, 2.300h)
    
    Retorne EXATAMENTE e APENAS um JSON puro (sem blocos de código markdown como ```json) com as chaves:
    "nick", "nivel", "horas".
    Exemplo:
    {{"nick": "zigue", "nivel": "Level 10", "horas": "1.500h"}}
    
    Se não encontrar algum valor, retorne "Desconhecido".
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )
        
        texto_limpo = re.sub(r'```json|```', '', response.text).strip()
        dados = json.loads(texto_limpo)
        return dados
    except Exception as e:
        return {"nick": f"Player {gc_id}", "nivel": "Lvl 10", "horas": "Desconhecido"}