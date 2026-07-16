# models.py
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

#Enumerado para la columna origen_datos
class EstadoOrigen(enum.Enum):
    PENDIENTE = "pendiente_inicializacion"
    ESTIMADO = "estimated_52w_high"
    VERIFICADO = "verified"

class Activo(Base):
    """Tabla estática con la información invariable de los activos."""
    __tablename__ = 'activos'
    
    ticker = Column(String(20), primary_key=True, comment="Símbolo del activo (ej: AAPL)")
    isin = Column(String(12), unique=True, nullable=False, comment="Código universal para Tradegate")
    nombre = Column(String(100), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(50))    
    # Relaciones bidireccionales
    seguimiento = relationship("Seguimiento", back_populates="activo", uselist=False, cascade="all, delete-orphan")
    transacciones = relationship("Transaccion", back_populates="activo", cascade="all, delete-orphan")

class Transaccion(Base):
    """Tabla de auditoría para registrar cada compra/venta."""
    __tablename__ = 'transacciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), ForeignKey('activos.ticker'), nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad = Column(Float, nullable=False)

    activo = relationship("Activo", back_populates="transacciones")

class Seguimiento(Base):
    """Tabla dinámica que el 'Agente Scraper' actualizará constantemente."""
    __tablename__ = 'seguimiento'
    
    ticker = Column(String(20), ForeignKey('activos.ticker'), primary_key=True)
    precio_base_cero = Column(Float, default=0.0, comment="Precio en la Fecha Cero")
    max_registrado = Column(Float, default=0.0, comment="Máximo desde la Fecha Cero")
    porcentaje_stop = Column(Float, default=0.2, comment="trailing stop personalizado")
    trailing_stop_price = Column(Float, default=0.0, comment="Nivel de salto del stop")
    origen_datos = Column(
        Enum(EstadoOrigen), 
        default=EstadoOrigen.PENDIENTE, 
        nullable=False,
        comment="Calidad del dato: obtenido directamente, calculado del máximo de las últimas 52 semanas, ..."
    )
    ultimo_precio_leido = Column(Float, default=0.0)

    activo = relationship("Activo", back_populates="seguimiento")