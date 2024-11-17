from app import db
from datetime import datetime
from extensions import db


class Club(db.Model):
    __tablename__ = 'clubes'
    
    id_club = db.Column(db.Integer, primary_key=True)
    codigo_club = db.Column(db.String(10), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    productos = db.relationship('Producto', backref='club', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def generar_codigo():
        """Genera un código único para el club"""
        ultimo_club = Club.query.order_by(Club.id_club.desc()).first()
        num = 1 if not ultimo_club else ultimo_club.id_club + 1
        return f"CLUB{num:03d}"

    @property
    def num_productos(self):
        """Retorna el número de productos del club"""
        return len(self.productos)

    def to_dict(self):
        return {
            'id_club': self.id_club,
            'codigo_club': self.codigo_club,
            'nombre': self.nombre,
            'num_productos': self.num_productos,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }