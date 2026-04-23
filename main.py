import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq Setup
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Usamos el modelo más avanzado solicitado
MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"

app = FastAPI(title="Facturas AI API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    text: str

class QueryRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = []
    image_base64: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Facturas AI - Chatbot Activo (Version Llama 4 Scout)"}

@app.post("/api/query")
async def query_invoices(request: QueryRequest):
    """
    Endpoint principal que soporta imágenes y memoria.
    """
    try:
        messages = []
        
        # System prompt
        messages.append({
            "role": "system", 
            "content": "Eres 'Facturas AI', un asistente experto en finanzas. Ayuda al usuario analizando sus facturas y respondiendo preguntas de forma profesional y amable."
        })

        # Memoria del chat
        if request.history:
            for msg in request.history:
                role = "assistant" if msg.get("role") == "assistant" else "user"
                messages.append({
                    "role": role,
                    "content": msg.get("text", "")
                })

        # Pregunta actual + Imagen
        if request.image_base64:
            content = [
                {"type": "text", "text": request.question},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}
                }
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": request.question})

        # Llamada a Groq
        response = groq_client.chat.completions.create(
            messages=messages,
            model=MODEL_ID,
        )
        
        answer = response.choices[0].message.content.strip()
        
        return {
            "status": "success", 
            "answer": answer,
            "model_used": MODEL_ID
        }

    except Exception as e:
        print(f"ERROR EN EL BACKEND: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
