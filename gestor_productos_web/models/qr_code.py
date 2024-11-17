from app import db
from datetime import datetime
import qrcode
from io import BytesIO
import base64

class CodigoQR(db.Model):
    __tablename__ = 'codigos_qr'
    
    id_qr = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(256), unique=True, nullable=False)
    codigo_producto = db.Column(db.String(100), db.ForeignKey('productos.codigo_producto'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_uso = db.Column(db.DateTime)

    @staticmethod
    def generar_codigo(codigo_producto):
        """Genera un código QR único basado en el código del producto"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"QR-{codigo_producto}-{timestamp}"

    def generar_imagen_qr(self):
        """Genera una imagen QR a partir del código"""
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
        """Genera y devuelve la imagen QR en formato base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def registrar_uso(self):
        """Registra el uso del código QR"""
        self.ultimo_uso = datetime.utcnow()
        db.session.commit()

    def toggle_estado(self):
        """Cambia el estado activo/inactivo del código QR"""
        self.activo = not self.activo
        db.session.commit()
        return self.activo

    def to_dict(self):
        return {
            'id_qr': self.id_qr,
            'codigo': self.codigo,
            'codigo_producto': self.codigo_producto,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None,
            'imagen_qr': f"data:image/png;base64,{self.get_imagen_base64()}"
        }