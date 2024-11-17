from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Importar y registrar blueprints
    from api.qr_validator import qr_bp
    app.register_blueprint(qr_bp)

    # Importar modelos
    from models.club import Club
    from models.producto import Producto
    from models.qr_code import CodigoQR

    # Crear tablas
    with app.app_context():
        db.create_all()

    return app