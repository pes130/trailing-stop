import csv
from datetime import datetime
from database import get_session, init_db
from models import Activo, Seguimiento, Transaccion, EstadoOrigen

def cargar_datos_csv(ruta_archivo):
    init_db()

    with get_session() as session:
        with open(ruta_archivo, mode='r', encoding='utf-8') as archivo:
            lector = csv.DictReader(archivo, delimiter=';')
            
            for fila in lector:
                ticker = fila['ticker'].strip()
                
                activo_existente = session.query(Activo).filter_by(ticker=ticker).first()
                if activo_existente:
                    print(f"El activo {ticker} ya existe. Saltando...")
                    continue
                
                print(f"Procesando {ticker}...")

                # --- LIMPIEZA Y TRANSFORMACIÓN ---
                precio_compra = float(fila['precio_compra_medio'].replace(',', '.'))
                # Asumimos que la primera vez, el base_cero es igual al de compra
                precio_base = precio_compra 
                cantidad = float(fila['cantidad'].replace(',', '.'))
                
                max_registrado = float(fila['max_registrado'].replace(',', '.'))
                max_historico = float(fila['max_historico'].replace(',', '.'))
                fecha_compra = datetime.strptime(fila['fecha_compra_inicial'].strip(), '%Y-%m-%d')
                
                estado_texto = fila['origen_datos'].strip().upper()
                origen_enum = getattr(EstadoOrigen, estado_texto, EstadoOrigen.PENDIENTE)

                porcentaje_stop = float(fila['porcentaje_stop'].replace(',', '.'))
                trailing_stop = max_registrado * (1 - porcentaje_stop)

                # --- CREACIÓN DE OBJETOS ---
                
                # A) La Caja Fuerte (Tabla Activo)
                nuevo_activo = Activo(
                    ticker=ticker,
                    isin=fila['isin'].strip(),
                    nombre=fila['nombre'].strip(),
                    exchange=fila['exchange'].strip(),
                    sector=fila['sector'].strip(),
                    precio_base_cero=precio_base,
                    precio_compra_medio=precio_compra,
                    cantidad_acciones=cantidad,
                    activa=True
                )
                
                session.add(nuevo_activo)
                session.flush() # Obligatorio para obtener el nuevo_activo.id

                # B) La Transacción Inicial
                nueva_transaccion = Transaccion(
                    ticker=ticker,
                    fecha=fecha_compra,
                    precio_unitario=precio_compra,
                    cantidad=cantidad 
                )

                # C) La Trinchera (Tabla Seguimiento, aislada de la contabilidad)
                nuevo_seguimiento = Seguimiento(
                    activo_id=nuevo_activo.id,
                    max_registrado=max_registrado,
                    max_historico=max_historico,
                    porcentaje_stop=porcentaje_stop,
                    trailing_stop_price=trailing_stop,
                    origen_datos=origen_enum,
                    ultimo_precio_leido=precio_compra
                )

                session.add(nueva_transaccion)
                session.add(nuevo_seguimiento)
            
            session.commit()
                
    print("\n¡Importación completada con éxito! Todos los datos están en su sitio.")

if __name__ == '__main__':
    cargar_datos_csv('activos.csv')