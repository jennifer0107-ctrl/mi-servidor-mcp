import os
import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# 1. Creamos la app de FastAPI que Render mantendrá viva en la web
app = FastAPI(title="Estacion_AutoMind_API")

# 2. Inicializamos el servidor MCP para estructurar las herramientas
mcp = FastMCP("Estacion_AutoMind")

# Credenciales de tu canal de ThingSpeak
CHANNEL_ID = "3370492"
READ_API_KEY = "85PT6XBHJ81R7MB3"

@mcp.tool()
def consultar_clima_actual() -> str:
    """Consulta en tiempo real las últimas lecturas de temperatura, humedad y presión de la estación AutoMind."""
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1&api_key={READ_API_KEY}"
    
    try:
        respuesta = requests.get(url)
        datos = respuesta.json()
        ultimo_feed = datos["feeds"][0]
        
        reporte = (
            f"--- DATOS EN VIVO DESDE LA NUBE ---\n"
            f"ID de Registro: {ultimo_feed['entry_id']}\n"
            f"Fecha y Hora (UTC): {ultimo_feed['created_at']}\n"
            f"Temperatura Actual: {ultimo_feed['field1']} °C\n"
            f"Humedad Relativa: {ultimo_feed['field2']} %\n"
            f"Presión Barométrica: {ultimo_feed['field3']} hPa\n"
            f"--------------------------------"
        )
        return reporte
        
    except Exception as error:
        return f"Error al conectar con ThingSpeak: {str(error)}"

# 3. Creamos las rutas web para que Render vea que el servicio responde con éxito
@app.get("/")
def inicio():
    return {"estado": "online", "servidor": "Estacion_AutoMind MCP a través de FastAPI"}

@app.get("/mcp")
def obtener_herramientas():
    """Ruta opcional para visualizar la metadata del servidor MCP."""
    return {"servidor": mcp.name, "herramientas": ["consultar_clima_actual"]}

if __name__ == "__main__":
    import uvicorn
    # Render asigna dinámicamente un puerto en la variable de entorno PORT
    puerto = int(os.environ.get("PORT", 8000))
    # Iniciamos uvicorn para escuchar las peticiones web
    uvicorn.run(app, host="0.0.0.0", port=puerto)
