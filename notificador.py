import os
import requests
from dotenv import load_dotenv


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
        return
    
    mensaje_texto = "".join(alertas)
       

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje_texto,
        "parse_mode": "Markdown"
    }

    try:
        respuesta = requests.post(url, json=payload, timeout=15)
        respuesta.raise_for_status()
    except Exception as e:
        print(f"Error al enviar mensaje por Telegram: {e}")

