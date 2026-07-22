import logging
from database import get_session
from models import Activo
import requests
import json
import os
from dotenv import load_dotenv

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Agente_Calculador")
# Cargamos las variables secretas al arrancar el script
load_dotenv()

def enviar_alerta_telegram(alertas):
    """
    Envía un mensaje directo a Telegram usando la API oficial.
    """
    if not alertas:
        return

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("Faltan credenciales de Telegram en el archivo .env")
        return

    logger.info("Enviando alerta directa a Telegram...")
    
    # Construimos el mensaje con un poco de formato
    mensaje_texto = "🚨 *ALERTA DE TRAILING STOP* 🚨\n\n"
    for alerta in alertas:
         mensaje_texto += f"📉 *{alerta['nombre']}* ({alerta['ticker']})\n"
         mensaje_texto += f"• Precio Actual: `{alerta['precio_actual']}`\n"
         mensaje_texto += f"• Stop Loss: `{alerta['stop_price']}`\n"
         mensaje_texto += f"• Caída desde máximo: `{alerta['caida_desde_maximo']}%`\n\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje_texto,
        "parse_mode": "Markdown"
    }

    try:
        respuesta = requests.post(url, json=payload, timeout=15)
        respuesta.raise_for_status()
        logger.info("Mensaje de Telegram enviado con éxito.")
    except Exception as e:
        logger.error(f"Error al enviar mensaje por Telegram: {e}")

def evaluar_trailing_stops():
    logger.info("Iniciando evaluación de Trailing Stops...")
    alertas_generadas = []

    with get_session() as session:
        activos = session.query(Activo).filter_by(activa=True).all()

        for activo in activos:
            seguimiento = activo.seguimiento
            
            # Verificaciones de seguridad básicas
            if not seguimiento or seguimiento.ultimo_precio_leido <= 0:
                logger.warning(f"[{activo.ticker}] {activo.nombre}: Sin datos de precio actual válidos. Saltando.")
                continue

            precio_actual = seguimiento.ultimo_precio_leido
            stop_price = seguimiento.trailing_stop_price

            # Lógica central del sistema
            if precio_actual <= stop_price:
                logger.warning(f"¡ALERTA! [{activo.nombre}] ha cruzado su Trailing Stop.")
                logger.warning(f"   -> Precio Actual: {precio_actual} | Stop Loss: {stop_price}")
                
                # Guardamos la alerta para pasarla al siguiente agente
                alertas_generadas.append({
                    "ticker": activo.ticker,
                    "nombre": activo.nombre,
                    "precio_actual": precio_actual,
                    "stop_price": stop_price,
                    "caida_desde_maximo": round(((seguimiento.max_registrado - precio_actual) / seguimiento.max_registrado) * 100, 2)
                })
            else:
                margen = round(((precio_actual - stop_price) / stop_price) * 100, 2)
                logger.info(f"[{activo.nombre}] Zona segura. A un {margen}% de tocar el stop.")

    if not alertas_generadas:
        logger.info("Evaluación finalizada. Ningún activo ha tocado su stop loss.")
    else:
        logger.info(f"Evaluación finalizada. Se han detectado {len(alertas_generadas)} alertas críticas.")
    
    if not alertas_generadas:
        logger.info("Evaluación finalizada. Ningún activo ha tocado su stop loss.")
    else:
        logger.info(f"Evaluación finalizada. Se han detectado {len(alertas_generadas)} alertas críticas.")
        enviar_alerta_telegram(alertas_generadas)

    return alertas_generadas

if __name__ == '__main__':
    alertas = evaluar_trailing_stops()