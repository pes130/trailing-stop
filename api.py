from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Activo

# Inicializamos la API
app = FastAPI(
    title="Secretario Financiero API",
    description="API de lectura segura para el Agente IA de la cartera",
    version="1.0.0"
)

# Dependencia para abrir y cerrar la conexión a la base de datos de forma segura
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- NUESTRO PRIMER ENDPOINT (Solo Lectura) ---

@app.get("/api/cartera", summary="Obtener el estado de los activos vivos")
def obtener_cartera(db: Session = Depends(get_db)):
    """
    Devuelve una lista con las acciones activas, su precio medio de compra y el último precio leído.
    El Agente usará esto para calcular rentabilidades.
    """
    activos = db.query(Activo).filter_by(activa=True).all()
    
    if not activos:
        raise HTTPException(status_code=404, detail="No hay activos en la cartera.")
    
    resultado = []
    for activo in activos:
        # Extraemos solo lo necesario para el Agente
        seguimiento = activo.seguimiento
        precio_actual = seguimiento.ultimo_precio_leido if seguimiento else None
        stop_loss = seguimiento.trailing_stop_price if seguimiento else None
        
        resultado.append({
            "ticker": activo.ticker,
            "nombre": activo.nombre,
            "cantidad": activo.cantidad_acciones,
            "precio_compra_medio": activo.precio_compra_medio,
            "precio_actual": precio_actual,
            "stop_loss": stop_loss,
            "maximo_historico": seguimiento.max_historico
        })
        
    return {"activos": resultado}


@app.get("/api/stops", summary="Obtener el listado de stops de mis activos")
def obtener_stops(db: Session = Depends(get_db)):
    activos = db.query(Activo).filter_by(activa=True).all()
    
    if not activos:
        raise HTTPException(status_code=404, detail="No hay activos en la cartera.")
    
    resultado = []
    for activo in activos:
        # Extraemos solo lo necesario para el Agente
        seguimiento = activo.seguimiento
        precio_actual = seguimiento.ultimo_precio_leido if seguimiento else None
        stop_loss = seguimiento.trailing_stop_price if seguimiento else None
        
        resultado.append({
            "ticker": activo.ticker,
            "nombre": activo.nombre,
            "stop_loss": stop_loss
        })
        
    return {"activos": resultado}