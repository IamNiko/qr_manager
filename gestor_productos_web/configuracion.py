from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Configuracion:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CLAVE_TECNICA = os.getenv('TECH_ACCESS_KEY')
    
    # Configuración de rutas
    BASE_DIR = Path(__file__).resolve().parent
    DB_DIR = BASE_DIR / "base_datos"
    URL_BASE_DATOS = f"sqlite:///{DB_DIR}/database.db"
    
    
    # Configuración de Mensajes
    LONGITUD_MAXIMA_MENSAJE = 1500

configuracion = Configuracion()