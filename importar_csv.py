import csv
from datetime import datetime
from database import get_session, init_db
from models import Activo, Seguimiento, Transaccion, EstadoOrigen

def cargar_datos_csv(ruta_archivo):
    # 1. Asegurar que las tablas físicas están creadas
    init_db()

    # 2. Usar tu context manager seguro
    with get_session() as session:
        # Abrir el CSV indicando el delimitador ';'
        with open(ruta_archivo, mode='r', encoding='utf-8') as archivo:
            lector = csv.DictReader(archivo, delimiter=';')
            
            for fila in lector:
                ticker = fila['ticker'].strip()
                
                # Comprobar si el activo ya existe para no duplicarlo
                activo_existente = session.query(Activo).filter_by(ticker=ticker).first()
                if activo_existente:
                    print(f"El activo {ticker} ya existe. Saltando...")
                    continue
                
                print(f"Procesando {ticker}...")

                # --- LIMPIEZA Y TRANSFORMACIÓN DE DATOS ---
                # Reemplazar la coma por punto para que Python entienda los decimales
                precio_compra = float(fila['precio_compra_medio'].replace(',', '.'))
                max_registrado = float(fila['max_registrado'].replace(',', '.'))
                
                # Parsear la fecha del formato YYYY-MM-DD
                fecha_compra = datetime.strptime(fila['fecha_compra_inicial'].strip(), '%Y-%m-%d')
                
                # Mapear el texto del CSV al Enumerado seguro
                estado_texto = fila['origen_datos'].strip().upper()
                origen_enum = getattr(EstadoOrigen, estado_texto, EstadoOrigen.PENDIENTE)

                # Calcular el nivel de Stop Loss inicial (un porcentaje_stop% por debajo del máximo)
                porcentaje_stop = float(fila['porcentaje_stop'].replace(',', '.'))
                trailing_stop = max_registrado * (1-porcentaje_stop)

                # --- CREACIÓN DE OBJETOS SQLALCHEMY ---
                
                # A) El Activo (Tabla estática)
                nuevo_activo = Activo(
                    ticker=ticker,
                    isin=fila['isin'].strip(),
                    nombre=fila['nombre'].strip(),
                    exchange=fila['exchange'].strip(),
                    sector=fila['sector'].strip()
                )

                # B) La Transacción de "Reset" (Tabla de auditoría)
                # Ponemos cantidad=1.0 simbólicamente como base de la posición
                nueva_transaccion = Transaccion(
                    ticker=ticker,
                    fecha=fecha_compra,
                    precio_unitario=precio_compra,
                    cantidad=1.0 
                )

                # C) El Seguimiento (Tabla dinámica para el Scraper)
                nuevo_seguimiento = Seguimiento(
                    ticker=ticker,
                    precio_base_cero=precio_compra,
                    max_registrado=max_registrado,
                    porcentaje_stop=porcentaje_stop,
                    trailing_stop_price=trailing_stop,
                    origen_datos=origen_enum,
                    ultimo_precio_leido=precio_compra # De momento, es el mismo
                )

                # Añadir los tres objetos a la sesión
                session.add(nuevo_activo)
                session.add(nueva_transaccion)
                session.add(nuevo_seguimiento)
                
    print("\n¡Importación completada con éxito! Todos los datos están en la BD.")

if __name__ == '__main__':
    cargar_datos_csv('activos.csv')