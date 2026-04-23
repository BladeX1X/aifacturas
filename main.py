import os
import json
import functions_framework
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicialización
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Modelo Multimodal y con Memoria
MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"

@functions_framework.http
def chat_handler(request):
    """
    Controlador para Google Cloud Functions que soporta:
    - Chat con memoria (history)
    - Análisis de imágenes (base64)
    - Modelo Llama 4 Scout
    """
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }

    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return (json.dumps({"error": "No JSON received"}), 400, headers)

        question = request_json.get('question', 'Analiza esto')
        history = request_json.get('history', [])
        image_base64 = request_json.get('image_base64')

        messages = []
        
        # System prompt
        messages.append({
            "role": "system", 
            "content": "Eres 'Facturas AI', un asistente experto en finanzas. Ayuda al usuario analizando sus facturas y respondiendo preguntas."
        })

        # Memoria del chat
        for msg in history:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            messages.append({
                "role": role,
                "content": msg.get("text", "")
            })

        # Pregunta actual + Imagen
        if image_base64:
            content = [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": question})

        # Llamada a Groq
        response = groq_client.chat.completions.create(
            messages=messages,
            model=MODEL_ID,
        )
        
        answer = response.choices[0].message.content.strip()
        
        return (json.dumps({
            "status": "success", 
            "answer": answer,
            "model_used": MODEL_ID
        }), 200, headers)

    except Exception as e:
        return (json.dumps({"error": str(e)}), 500, headers)
