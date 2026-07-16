import httpx
from bs4 import BeautifulSoup
import time
import logging
from database import get_session
from models import Activo
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Scraper_Tradegate")

def limpiar_precio(precio_str):
    try:
        if not precio_str: return None
        return float(precio_str.replace(' ', ''))
    except ValueError:
        return None

def obtener_datos_tradegate(isin):
    # Forzamos el dominio principal que sabemos que resuelve bien en tu SO
    url = f"https://www.tradegate.de/orderbuch.php?lang=en&isin={isin}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-GPC': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

    try:
        # ¡La magia está aquí! Activamos HTTP/2 explícitamente
        with httpx.Client(http2=True, headers=headers, timeout=15.0, follow_redirects=True) as client:
            respuesta = client.get(url)
            respuesta.raise_for_status()
            
            sopa = BeautifulSoup(respuesta.text, 'html.parser')
            
            nodo_last = sopa.find(id='last')
            nodo_high = sopa.find(id='high')
            
            if not nodo_last or not nodo_high:
                return None, None

            return limpiar_precio(nodo_last.text), limpiar_precio(nodo_high.text)

    except Exception as e:
        logger.error(f"Error de conexión al raspar {isin}: {e}")
        return None, None

def ejecutar_scraper():
    logger.info("Iniciando ronda de web scraping (HTTP/2)...")
    
    with get_session() as db_session:
        activos = db_session.query(Activo).all()
        
        if not activos:
            logger.info("No hay activos en la base de datos para escanear.")
            return

        for activo in activos:
            seguimiento = activo.seguimiento
            logger.info(f"Consultando {activo.nombre} (ISIN: {activo.isin})...")
            
            last, high = obtener_datos_tradegate(activo.isin)
            
            if last is None or high is None:
                logger.error(f"Saltando {activo.nombre} por falta de datos.")
                # Si hay error, también hacemos la pausa aleatoria para no saturar reintentos
                time.sleep(random.uniform(5, 10))
                continue

            seguimiento.ultimo_precio_leido = last
            logger.info(f"[{activo.nombre}] Precio actual (Last): {last}")

            if high > seguimiento.max_registrado:
                logger.info(f"¡NUEVO MÁXIMO para {activo.nombre}! Anterior: {seguimiento.max_registrado} -> Nuevo: {high}")
                seguimiento.max_registrado = high
                
                nuevo_stop = high * (1 - seguimiento.porcentaje_stop)
                seguimiento.trailing_stop_price = nuevo_stop
                logger.info(f"Stop loss actualizado a: {nuevo_stop:.2f}")

            # --- PAUSA ALEATORIA ---
            pausa = random.uniform(5, 10)
            logger.debug(f"Pausa orgánica de {pausa:.2f} segundos...")
            time.sleep(pausa)

    logger.info("Ronda de scraping finalizada con éxito.")

if __name__ == '__main__':
    ejecutar_scraper()