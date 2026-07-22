from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base,relationship
import enum

Base = declarative_base()

class EstadoOrigen(enum.Enum):
    MANUAL = "MANUAL"
    SCRAPER = "SCRAPER"
    PENDIENTE = "PENDIENTE"

class Activo(Base):
    __tablename__ = 'activos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    isin = Column(String(50), nullable=True)
    nombre = Column(String(100), nullable=True)
    exchange = Column(String(50), nullable=True)
    sector = Column(String(50), nullable=True)
    precio_base_cero = Column(Float, nullable=False)    # El precio de compra inicial/original
    precio_compra_medio = Column(Float, nullable=True)  # precio de compra promediado
    cantidad_acciones = Column(Float, default=0.0)      
    activa = Column(Boolean, default=True)             
    
    seguimiento = relationship("Seguimiento", back_populates="activo", uselist=False,cascade="all, delete-orphan")

class Seguimiento(Base):
    __tablename__ = 'seguimiento'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    activo_id = Column(Integer, ForeignKey('activos.id'), nullable=False)
    ultimo_precio_leido = Column(Float, nullable=True)
    max_registrado = Column(Float, nullable=False) # Máximo desde que se compró
    max_historico = Column(Float, nullable=True) # Máximo histórico
    porcentaje_stop = Column(Float, nullable=False, default=0.20)
    trailing_stop_price = Column(Float, nullable=False)
    
    origen_datos = Column(Enum(EstadoOrigen), default=EstadoOrigen.PENDIENTE)
    
    activo = relationship("Activo", back_populates="seguimiento")

class Transaccion(Base):
    __tablename__ = 'transacciones'
    # (Mantén esta tabla exactamente igual que la tenías, no necesita cambios)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    fecha = Column(DateTime, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad = Column(Float, nullable=False)