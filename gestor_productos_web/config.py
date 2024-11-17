import os

class Config:
    # Configuración básica
    SECRET_KEY = 'tu_clave_secreta_aqui'
    BASE_DIR = r"C:/Users/nicol/QR_PROJ/gestor_productos_web"
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'productos_por_clubes.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Otras configuraciones
    DEBUG = True
    TESTING = False