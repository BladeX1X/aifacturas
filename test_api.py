import requests
import json

url = "http://localhost:8080/api/query"
payload = {
    "question": "Hola, ¿quién eres?",
    "history": []
}

try:
    # Asegúrate de que el backend esté corriendo localmente para probar
    # O cambia la URL a la de producción para ver el error real
    prod_url = "https://chat-handler-189530299276.northamerica-south1.run.app/api/query"
    response = requests.post(prod_url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
