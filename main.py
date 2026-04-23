import os
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Groq Setup
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"

# Supabase Setup (Opcional por ahora)
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_client():
    if not supabase_url or not supabase_url.startswith("http"):
        print("Aviso: Supabase no está configurado o la URL es inválida. Saltando conexión.")
        return None
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return None

supabase = get_supabase_client()

app = FastAPI(title="Facturas AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Concepto(BaseModel):
    descripcion: str
    cantidad: float
    precio_unitario: float
    importe: float

class Factura(BaseModel):
    comercio: str
    rfc_emisor: Optional[str] = None
    fecha: str
    total: float
    impuestos: float
    conceptos: List[Concepto] = []

@app.get("/")
def read_root():
    return {"message": "Facturas AI - Chatbot Activo"}

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
async def query_invoices(request: QueryRequest):
    """
    Endpoint principal del chatbot.
    """
    try:
        # Schema info provided to Gemini to help it understand what it can do
        schema = """
        Tablas disponibles (si Supabase está conectado):
        1. facturas: id, comercio, rfc_emisor, fecha (YYYY-MM-DD), total, impuestos
        2. conceptos: id, factura_id, descripcion, cantidad, precio_unitario, importe
        """
        
        prompt = f"""
        Eres 'Facturas AI', un asistente virtual inteligente, amable y profesional especializado en finanzas personales y gestión de facturas.
        
        Tu objetivo es ayudar al usuario con cualquier duda que tenga. 
        - Si te saludan, responde de forma cálida.
        - Si preguntan sobre sus gastos o facturas, intenta generar una consulta SQL basada en este esquema:
        {schema}
        - Si no tienes acceso a la base de datos (Supabase no configurado), explícalo amablemente y ofrece ayuda general.
        
        Formatos de respuesta obligatorios:
        1. Para SQL: {{"type": "sql", "query": "SELECT ..."}}
        2. Para texto directo: {{"type": "text", "answer": "Tu respuesta aquí"}}
        
        Pregunta del usuario: "{request.question}"
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        content = response.choices[0].message.content.strip()
        
        # Limpieza de JSON si Gemini incluyó markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {"status": "success", "answer": content} # Fallback to raw text
        
        if data.get("type") == "text" or "answer" in data:
            return {"status": "success", "answer": data.get("answer", content)}
        
        # Ejecución de SQL si aplica
        if data.get("type") == "sql" and supabase:
            try:
                res = supabase.rpc("execute_sql", {"query": data["query"]}).execute()
                result_str = json.dumps(res.data)
                summary_prompt = f"Explica estos datos de forma natural al usuario: {result_str}. Pregunta original: '{request.question}'"
                summary_res = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": summary_prompt}],
                    model=GROQ_MODEL,
                )
                return {"status": "success", "answer": summary_res.choices[0].message.content}
            except Exception as sql_err:
                return {"status": "success", "answer": f"Lo siento, tuve un problema al consultar tus datos: {str(sql_err)}"}
        
        return {"status": "success", "answer": data.get("answer", "No estoy seguro de cómo responder a eso, pero estoy aquí para ayudarte.")}
        
    except Exception as e:
        print(f"ERROR EN EL CHATBOT: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el chatbot: {str(e)}")

