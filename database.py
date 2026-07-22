# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
import os
from models import Base


# Configuración de logging 
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DB_Manager")

DB_PATH = os.getenv("DB_PATH", "trailing_stop.db")

# echo=False para producción. Cámbialo a True si quieres ver las consultas SQL nativas en la consola al debugear.
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea todas las tablas basándose en los modelos importados."""
    try:
        # Importante: Base.metadata.create_all necesita que los modelos estén definidos
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos y tablas inicializadas correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise

@contextmanager
def get_session():
    """Context manager para operaciones seguras (Unit of Work pattern)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Error en la transacción, haciendo rollback: {e}")
        session.rollback()
        raise
    finally:
        session.close()