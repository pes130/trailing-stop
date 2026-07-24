import logging
from database import get_session
from models import Activo
from notificador import enviar_alerta_telegram

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Agente_Calculador")


def construir_mensaje_stop(datos):
    mensaje_texto =""
    mensaje_texto += f"📉 *{datos['nombre']}* ({datos['ticker']})\n"
    mensaje_texto += f"• Precio Actual: {datos['precio_actual']}\n"
    mensaje_texto += f"• Stop Loss: {datos['stop_price']}\n"
    mensaje_texto += f"• Caída desde máximo: {datos['caida_desde_maximo']}%\n\n"
    mensaje_texto += f"\n"
    return mensaje_texto

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
                alerta_stop = construir_mensaje_stop({
                    "ticker": activo.ticker,
                    "nombre": activo.nombre,
                    "precio_actual": precio_actual,
                    "stop_price": stop_price,
                    "caida_desde_maximo": round(((seguimiento.max_registrado - precio_actual) / seguimiento.max_registrado) * 100, 2)
                })
                alertas_generadas.append(alerta_stop)
            else:
                margen = round(((precio_actual - stop_price) / stop_price) * 100, 2)
                logger.info(f"[{activo.nombre}] Zona segura. A un {margen}% de tocar el stop.")
   
    if not alertas_generadas:
        logger.info("Evaluación finalizada. Ningún activo ha tocado su stop loss.")

        
    if alertas_generadas:
        logger.info(f"Evaluación finalizada. Se han detectado {len(alertas_generadas)} alertas críticas.")
        alertas_generadas.insert(0, "🚨 *TRAILING STOPS ALCANZADOS!* 🚨\n\n")
        enviar_alerta_telegram(alertas_generadas)

    return alertas_generadas

if __name__ == '__main__':
    alertas = evaluar_trailing_stops()