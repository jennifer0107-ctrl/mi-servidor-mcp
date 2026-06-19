import os
import requests
from mcp.server.fastmcp import FastMCP

# Inicializamos el servidor FastMCP estándar
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

if __name__ == "__main__":
    # Importación interna para asegurar compatibilidad con el entorno de Render
    from mcp.server.fastmcp.server import ASMServer
    
    # Forzamos a que corra como un servidor web HTTP en el puerto que pide Render
    puerto = int(os.environ.get("PORT", 8000))
    server = ASMServer(mcp)
    server.run(host="0.0.0.0", port=puerto, transport="http")
