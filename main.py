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
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("WARNING: GROQ_API_KEY no configurada. El servicio fallará al procesar consultas.")
groq_client = Groq(api_key=api_key or "dummy_key")
# Usamos Llama 3.3 Versatile
MODEL_ID = "llama-3.3-70b-versatile"

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
    categories: Optional[List[str]] = []

@app.get("/")
def read_root():
    return {"message": "Facturas AI - Chatbot Activo (Version Llama 3.3)"}

import shutil
import tempfile
from fastapi import UploadFile, File, Form

@app.post("/api/voice")
async def process_voice(
    file: UploadFile = File(...),
    categories: str = Form(""),
    summary: str = Form("")
):
    """
    Recibe un archivo de audio, lo transcribe con Whisper y procesa el gasto o consulta.
    """
    temp_path = None
    try:
        # 1. Guardar archivo temporalmente
        suffix = os.path.splitext(file.filename)[1] or ".m4a"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        # 2. Transcribir con Groq Whisper Turbo
        with open(temp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_path, audio_file.read()),
                model="whisper-large-v3-turbo",
                language="es",
                response_format="text",
            )
        
        text_recognized = transcription.strip()
        print(f"TRANSCRIPCIÓN IA: {text_recognized}")

        # 3. Procesar el texto con el LLM (Llama 4 Scout)
        existing_cats = categories.split(',') if categories else []
        cat_context = f"Categorías existentes: {', '.join(existing_cats)}" if existing_cats else "No hay categorías previas."
        summary_context = f"Resumen financiero actual: {summary}" if summary else "No hay datos financieros previos."

        messages = [
            {
                "role": "system", 
                "content": f"""Eres 'Gastos AI', un asistente financiero personal inteligente.
                
                {summary_context}
                {cat_context}
                
                TU MISIÓN:
                1. Si el usuario describe un GASTO o INGRESO: Extrae los datos para guardarlos.
                   - Intenta encajar en categorías existentes.
                   - Clasifica como 'income' (ingreso) o 'expense' (gasto).
                   - El campo "answer" DEBE reflejar si es un ingreso o gasto (ej: "¡Vale! He registrado tu ingreso..." o "Gasto guardado correctamente...").
                2. Si el usuario hace una PREGUNTA (ej: "¿Cuánto he gastado?", "¿Cuál es mi saldo?"): Responde basándote en el 'Resumen financiero actual'.
                
                DEBES responder EXCLUSIVAMENTE con un JSON estructurado:
                {{
                  "answer": "Respuesta contextualizada",
                  "type": "transaction" | "query",
                  "transaction": {{
                    "amount": "XX.XX",
                    "type": "income" | "expense",
                    "category": "Categoría",
                    "title": "Descripción",
                    "emoji": "🍕"
                  }} | null
                }}
                Nota: Si detectas que es dinero que RECIBE el usuario, "type" SIEMPRE es "income".
                Si es una consulta, 'transaction' debe ser null y 'type' debe ser 'query'.
            },
            {"role": "user", "content": text_recognized}
        ]

        response = groq_client.chat.completions.create(
            messages=messages,
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "status": "success",
            "transcription": text_recognized,
            "data": result
        }

    except Exception as e:
        print(f"ERROR EN VOICE PROCESSING: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/query")
async def query_invoices(request: QueryRequest):
    """
    Endpoint principal que soporta imágenes, memoria y devuelve JSON estructurado.
    """
    try:
        messages = []
        
        # System prompt unificado con soporte para Transacciones y Consultas
        messages.append({
            "role": "system", 
            "content": f"""Eres 'Gastos AI', un asistente experto en finanzas personales.
                CONTEXTO:
                Categorías existentes: {', '.join(request.categories or [])}
                
                TU MISIÓN:
                1. Si el usuario describe un GASTO/INGRESO o sube una IMAGEN de un ticket/factura:
                   - Extrae los datos: monto, categoría, título (comercio), emoji.
                   - IMPORTANTE: Prioriza usar una de las CATEGORÍAS EXISTENTES si encaja. Si no, crea una nueva coherente.
                   - Clasifica como 'income' (ingreso) o 'expense' (gasto).
                   - Si es una imagen, sé preciso con los números que veas.
                2. Si la IMAGEN NO ES UNA FACTURA/TICKET:
                   - Responde con un comentario MUY CORTO (máximo 1 frase) e INGENIOSO/SARCÁSTICO.
                   - Ejemplos: '¿Un selfie? 10/10, pero sigo sin ver el ticket.', 'Lindo paisaje, pero no paga la renta.', 'Esto no es un ticket, es arte... pero no lo puedo sumar.', '¿Comida? ¡Qué hambre! Pero pásame el recibo.'.
                   - El "type" debe ser "query".
                3. Si el usuario hace una PREGUNTA: Responde de forma BREVE y precisa.
                
                DEBES responder EXCLUSIVAMENTE con un JSON estructurado:
                {{
                  "answer": "Tu respuesta amable o descripción del registro",
                  "type": "transaction" | "query",
                  "transaction": {{
                    "amount": "XX.XX",
                    "type": "income" | "expense",
                    "category": "Categoría",
                    "title": "Descripción",
                    "emoji": "🍕"
                  }} | null
                }}
                Nota: Si detectas que el usuario RECIBE dinero, "type" SIEMPRE es "income".
            """
        })

        # Memoria del chat (limitada para evitar tokens excesivos)
        if request.history:
            for msg in request.history[-5:]:
                role = "assistant" if msg.get("role") == "assistant" else "user"
                messages.append({
                    "role": role,
                    "content": msg.get("text", "")
                })

        # Pregunta actual + Imagen
        user_content = [{"type": "text", "text": request.question or "Analiza esta factura"}]
        
        if request.image_base64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}
            })
            # Forzamos modelo con visión si hay imagen
            current_model = "llama-3.2-11b-vision-preview"
        else:
            current_model = MODEL_ID

        messages.append({"role": "user", "content": user_content})

        # Llamada a Groq
        response = groq_client.chat.completions.create(
            messages=messages,
            model=current_model,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "status": "success", 
            "data": result,
            "model_used": current_model
        }

    except Exception as e:
        print(f"ERROR EN EL BACKEND: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
