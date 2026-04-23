# Facturas AI - Backend 🚀

Este es el microservicio encargado de procesar facturas utilizando Inteligencia Artificial. Actúa como puente entre la aplicación móvil y el modelo Llama 3.3 de Groq.

## 🛠️ Tecnologías
- **FastAPI**: Framework web moderno y de alto rendimiento.
- **Groq SDK**: Integración con modelos de lenguaje ultrarrápidos (Llama 3.3 70B).
- **Supabase**: Base de datos PostgreSQL para almacenamiento de facturas y ejecución de SQL dinámico.
- **Python 3.11+**

## 📂 Estructura del Proyecto
- `main.py`: Punto de entrada principal con FastAPI.
- `function_main.py`: Adaptación para Google Cloud Functions.
- `requirements.txt`: Dependencias del proyecto.
- `.env.example`: Plantilla para variables de entorno.

## 🚀 Instalación Local

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/BladeX1X/aifacturas
    cd aifacturas
    ```

2.  **Crear entorno virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno**:
    Crea un archivo `.env` basado en `.env.example` y añade tus llaves:
    ```text
    GROQ_API_KEY=tu_api_key_aqui
    SUPABASE_URL=tu_url_aqui
    SUPABASE_SERVICE_ROLE_KEY=tu_key_aqui
    ```

5.  **Correr el servidor**:
    ```bash
    uvicorn main:app --reload
    ```

## ☁️ Despliegue en Google Cloud Functions
El archivo `function_main.py` está listo para ser desplegado. Asegúrate de configurar las variables de entorno en la consola de Google Cloud.

---
*Desarrollado con ❤️ por Antigravity AI.*
