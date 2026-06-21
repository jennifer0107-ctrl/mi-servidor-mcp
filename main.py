from fastmcp import FastMCP
from dotenv import load_dotenv
import os
import requests
import statistics

load_dotenv()

# Configuración de ThingSpeak (Usa tus credenciales por defecto)
THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "3370492")
THINGSPEAK_READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "85PT6XBHJ81R7MB3")

mcp = FastMCP("MCP Estación Meteorológica")

def limpiar_valores(feeds, campo_field): 
    """
    Extrae y convierte a flotante los valores válidos de un field específico de ThingSpeak.
    """
    valores = []
    for x in feeds:
        valor = x.get(campo_field)
        if valor is not None and valor != "" and valor != "nan":
            try:
                valores.append(float(valor))
            except ValueError:
                continue
    return valores

def mapear_feed_a_supabase(feed):
    """
    Traduce el formato de ThingSpeak al formato esperado por el esquema del profesor
    (id, created_at, temp, humedad, presion, id_sensor)
    """
    if not feed:
        return {}
    return {
        "id": feed.get("entry_id"),
        "created_at": feed.get("created_at"),
        "temp": feed.get("field1"),       # Field 1 = Temperatura
        "humedad": feed.get("field2"),    # Field 2 = Humedad
        "presion": feed.get("field3"),    # Field 3 = Presión
        "id_sensor": "ESP32_WOKWI_AUTO"
    }

# ==========================
# FUNCIONES INTERNAS (Formato del Profesor)
# ==========================

def _obtener_ultima_lectura():
    url = f"https://api.thethingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"
    params = {"api_key": THINGSPEAK_READ_API_KEY} if THINGSPEAK_READ_API_KEY else {}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return {"mensaje": "Error al conectar con ThingSpeak"}
        
        data = response.json()
        if not data or "entry_id" not in data:
            return {"mensaje": "No hay lecturas registradas"}
            
        return mapear_feed_a_supabase(data)
    except Exception as e:
        return {"mensaje": f"Error de conexión: {str(e)}"}


def _obtener_ultimas_lecturas(limite=50):
    url = f"https://api.thethingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
    params = {"results": limite}
    if THINGSPEAK_READ_API_KEY:
        params["api_key"] = THINGSPEAK_READ_API_KEY

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []
        
        feeds = response.json().get("feeds", [])
        feeds_ordenados = list(reversed(feeds))
        return [mapear_feed_a_supabase(f) for f in feeds_ordenados]
    except Exception:
        return []


def _obtener_datos_grafico(limite=100):
    url = f"https://api.thethingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
    params = {"results": limite}
    if THINGSPEAK_READ_API_KEY:
        params["api_key"] = THINGSPEAK_READ_API_KEY

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []
        
        feeds = response.json().get("feeds", [])
        return [mapear_feed_a_supabase(f) for f in feeds]
    except Exception:
        return []


def _obtener_resumen_estacion(limite=100):
    datos = _obtener_ultimas_lecturas(limite)

    if not datos:
        return {"mensaje": "No hay datos"}

    temperaturas = limpiar_valores([{"f": d["temp"]} for d in datos], "f")
    humedades = limpiar_valores([{"f": d["humedad"]} for d in datos], "f")
    presiones = limpiar_valores([{"f": d["presion"]} for d in datos], "f")

    if not temperaturas or not humedades or not presiones:
        return {"mensaje": "Datos insuficientes para generar resumen estadístico"}

    return {
        "total_lecturas": len(datos),
        "temperatura_promedio": round(statistics.mean(temperaturas), 2),
        "temperatura_maxima": max(temperaturas),
        "temperatura_minima": min(temperaturas),
        "humedad_promedio": round(statistics.mean(humedades), 2),
        "humedad_maxima": max(humedades),
        "humedad_minima": min(humedades),
        "presion_promedio": round(statistics.mean(presiones), 2),
        "presion_maxima": max(presiones),
        "presion_minima": min(presiones)
    }


def _detectar_alertas():
    lectura = _obtener_ultima_lectura()

    if "mensaje" in lectura:
        return lectura

    alertas = []

    temp = float(lectura.get("temp") or 0)
    humedad = float(lectura.get("humedad") or 0)
    presion = float(lectura.get("presion") or 0)

    if temp >= 35:
        alertas.append("Temperatura alta")

    if temp <= 15:
        alertas.append("Temperatura baja")

    if humedad >= 85:
        alertas.append("Humedad elevada")

    if presion < 1000:
        alertas.append("Posible lluvia")

    return {
        "estado": "Con alertas" if alertas else "Normal",
        "alertas": alertas
    }


def _datos_para_dashboard(limite=100):
    return {
        "ultima_lectura": _obtener_ultima_lectura(),
        "resumen": _obtener_resumen_estacion(limite),
        "alertas": _detectar_alertas(),
        "historico": _obtener_datos_grafico(limite),
        "tabla": _obtener_ultimas_lecturas(limite)
    }

# ==========================
# HERRAMIENTAS MCP (Contrato del Profesor)
# ==========================

@mcp.tool()
def obtener_ultima_lectura():
    """
    Obtiene la lectura más reciente registrada por la estación meteorológica.

    Usar esta herramienta cuando el usuario pregunte por:
    - temperatura actual
    - humedad actual
    - presión actual
    - última lectura del sensor
    - estado actual de la estación meteorológica
    """
    return _obtener_ultima_lectura()


@mcp.tool()
def obtener_ultimas_lecturas(limite: int = 50):
    """
    Obtiene las últimas lecturas registradas en la estación meteorológica.
    """
    return _obtener_ultimas_lecturas(limite)


@mcp.tool()
def obtener_datos_grafico(limite: int = 100):
    """
    Obtiene datos meteorológicos preparados para construir gráficos.
    """
    return _obtener_datos_grafico(limite)


@mcp.tool()
def obtener_resumen_estacion(limite: int = 100):
    """
    Calcula un resumen estadístico de la estación meteorológica.
    """
    return _obtener_resumen_estacion(limite)


@mcp.tool()
def detectar_alertas():
    """
    Detecta alertas meteorológicas usando la última lectura registrada.
    """
    return _detectar_alertas()


@mcp.tool()
def datos_para_dashboard(limite: int = 100):
    """
    Obtiene todos los datos necesarios para construir un dashboard meteorológico completo.
    """
    return _datos_para_dashboard(limite)

@mcp.prompt()
def prompt_dashboard_personalizado(tipo_dashboard: str = "ejecutivo", limite: int = 100):
    return f"""
Utiliza la herramienta datos_para_dashboard(limite={limite}).

Crea un dashboard meteorológico de tipo: {tipo_dashboard}.

Incluye KPIs, gráficos interactivos, alertas automáticas, tabla de lecturas recientes y conclusiones.

Entrega el resultado como una página web completa en HTML, CSS y JavaScript.
"""
