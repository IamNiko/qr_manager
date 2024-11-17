from app import db
from datetime import datetime

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id_producto = db.Column(db.Integer, primary_key=True)
    codigo_producto = db.Column(db.String(20), unique=True, nullable=False)
    id_club = db.Column(db.Integer, db.ForeignKey('clubes.id_club'), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    pvp = db.Column(db.Float, nullable=False)
    costo = db.Column(db.Float, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    codigos_qr = db.relationship('CodigoQR', backref='producto', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def generar_codigo(id_club):
        """Genera un código único para el producto"""
        productos_club = Producto.query.filter_by(id_club=id_club).count()
        siguiente_num = productos_club + 1
        return f"PROD{int(id_club):03d}{siguiente_num:04d}"

    @property
    def margen(self):
        """Calcula el margen de ganancia"""
        if self.costo > 0:
            return ((self.pvp - self.costo) / self.costo) * 100
        return 0

    @property
    def num_qr(self):
        """Retorna el número de códigos QR asociados"""
        return len(self.codigos_qr)

    def to_dict(self):
        return {
            'id_producto': self.id_producto,
            'codigo_producto': self.codigo_producto,
            'marca': self.marca,
            'nombre': self.nombre,
            'pvp': float(self.pvp),
            'costo': float(self.costo),
            'margen': float(self.margen),
            'num_qr': self.num_qr,
            'club': self.club.nombre,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }