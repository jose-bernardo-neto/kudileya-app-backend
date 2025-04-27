from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
from pydantic import BaseModel
import os
import requests
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Depois pode restringir se quiser
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura a pasta templates
templates = Jinja2Templates(directory="templates")

class Pergunta(BaseModel):
    pergunta: str

@app.get("/keep-alive")
async def keep_alive():
    return {"status": "alive"}

@app.get("/faqs")
async def get_faqs():
    try:
        path = Path("data/faqs.json")
        with path.open("r", encoding="utf-8") as f:
            faqs = json.load(f)
        return JSONResponse(content=faqs)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/perguntar")
async def perguntar(pergunta: Pergunta):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "X-Title": "Kudileya"
            },
            json={
                "model": "openrouter/auto",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu és o Kudileya, um assistente jurídico criado por estudantes do Smartbits Usa linguagem simples e acessível.Confere sempre se a informação é válida e não dás conselhos jurídicos. Se não souberes a resposta, diz que não sabes. Sempre contextualize a resposta para Angola."
                    },
                    {
                        "role": "user",
                        "content": pergunta.pergunta
                    }
                ]
            }
        )

        data = response.json()
        if 'choices' not in data:
            raise HTTPException(status_code=500, detail=data)

        resposta = data['choices'][0]['message']['content']
        return {"resposta": resposta}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
