from app import db
from datetime import datetime
import random
import string
import qrcode
from io import BytesIO
import base64

class QREspecial(db.Model):
    __tablename__ = 'qr_especiales'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    codigo_producto = db.Column(db.String(20), db.ForeignKey('productos.codigo_producto'))
    credito_disponible = db.Column(db.Integer, nullable=False)
    fecha_caducidad = db.Column(db.Date, nullable=False)
    usos_maximos = db.Column(db.Integer, nullable=False)
    usos_actuales = db.Column(db.Integer, default=0)
    usos_restantes = db.Column(db.Integer, default=0)  # Nuevo campo agregado
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Relación con el producto
    producto = db.relationship('Producto', backref='qr_especiales')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Igualar usos_restantes al valor de usos_maximos al crear un nuevo QR especial
        self.usos_restantes = self.usos_maximos
    
    @staticmethod
    def generar_codigo_aleatorio(length=20):
        caracteres = string.ascii_uppercase + string.digits
        return ''.join(random.choice(caracteres) for _ in range(length))

    def generar_codigo_completo(self):
        codigo_aleatorio = self.generar_codigo_aleatorio()
        credito_disponible_formato = f"{self.credito_disponible:02d}"
        fecha_formato = self.fecha_caducidad.strftime("%Y%m%d")
        usos_formato = f"{self.usos_maximos:03d}"
        return f"{codigo_aleatorio}/{self.codigo_producto}/{credito_disponible_formato}/{fecha_formato}/{usos_formato}"

    def generar_imagen_qr(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.codigo)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def get_imagen_base64(self):
        img = self.generar_imagen_qr()
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def esta_caducado(self):
        return datetime.now().date() > self.fecha_caducidad

    def esta_agotado(self):
        return self.usos_actuales >= self.usos_maximos

    def es_valido(self):
        return self.activo and not self.esta_caducado() and not self.esta_agotado()

    def registrar_uso(self):
        if self.es_valido():
            self.usos_actuales += 1
            db.session.commit()
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'codigo_producto': self.codigo_producto,
            'credito_disponible': self.credito_disponible,
            'fecha_caducidad': self.fecha_caducidad.isoformat(),
            'usos_maximos': self.usos_maximos,
            'usos_actuales': self.usos_actuales,
            'usos_restantes': self.usos_restantes,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'activo': self.activo,
            'esta_caducado': self.esta_caducado(),
            'esta_agotado': self.esta_agotado(),
            'es_valido': self.es_valido()
        }
