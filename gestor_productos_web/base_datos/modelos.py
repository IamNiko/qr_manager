from sqlalchemy import Column, String, Integer, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Conversacion(Base):
    __tablename__ = "conversaciones"

    id = Column(Integer, primary_key=True, index=True)  # Clave primaria única
    remitente = Column(String, nullable=False)  # No es único, puede repetirse
    paso = Column(String, default="inicio")  # Paso actual en el flujo
    nombre = Column(String, nullable=True)  # Nombre del usuario
    rol = Column(String, nullable=True)  # Rol del usuario (jugador, staff, técnico)
    acceso_tecnico = Column(Boolean, default=False)  # Validación de acceso técnico
    historial_conversacion = Column(JSON, default="[]")  # Historial como texto o JSON
    mensaje = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)