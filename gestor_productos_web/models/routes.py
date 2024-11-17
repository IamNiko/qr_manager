from flask import Blueprint, request, jsonify, send_file
from models.qr_code import CodigoQR
from models.producto import Producto
from app import db
from io import BytesIO

api = Blueprint('api', __name__)

# @api.route('/api/validar_qr', methods=['POST'])
# def validar_qr():
#     """Valida un código QR y devuelve la información del producto"""
#     try:
#         data = request.get_json()
        
#         if not data or 'codigo_qr' not in data:
#             return jsonify({
#                 'valido': False,
#                 'mensaje': 'Código QR no proporcionado'
#             }), 400

#         qr = CodigoQR.query.filter_by(
#             codigo=data['codigo_qr']
#         ).first()

#         if not qr:
#             return jsonify({
#                 'valido': False,
#                 'mensaje': 'Código QR no encontrado'
#             }), 404

#         if not qr.activo:
#             return jsonify({
#                 'valido': False,
#                 'mensaje': 'Código QR inactivo'
#             }), 403

#         # Registrar uso
#         qr.registrar_uso()

#         return jsonify({
#             'valido': True,
#             'producto': {
#                 'codigo': qr.producto.codigo_producto,
#                 'marca': qr.producto.marca,
#                 'nombre': qr.producto.nombre,
#                 'pvp': float(qr.producto.pvp),
#                 'costo': float(qr.producto.costo),
#                 'club': qr.producto.club.nombre
#             },
#             'mensaje': 'Código QR válido'
#         })

#     except Exception as e:
#         return jsonify({
#             'valido': False,
#             'mensaje': f'Error: {str(e)}'
#         }), 500

@api.route('/api/qr/crear', methods=['POST'])
def crear_qr():
    """Crea un nuevo código QR para un producto"""
    try:
        data = request.get_json()
        
        if not data or 'codigo_producto' not in data:
            return jsonify({
                'exito': False,
                'mensaje': 'Código de producto no proporcionado'
            }), 400

        producto = Producto.query.filter_by(
            codigo_producto=data['codigo_producto']
        ).first()

        if not producto:
            return jsonify({
                'exito': False,
                'mensaje': 'Producto no encontrado'
            }), 404

        nuevo_qr = CodigoQR.crear_para_producto(data['codigo_producto'])

        return jsonify({
            'exito': True,
            'qr': nuevo_qr.to_dict(),
            'mensaje': 'Código QR creado exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'exito': False,
            'mensaje': f'Error: {str(e)}'
        }), 500

@api.route('/api/qr/<string:codigo>/toggle', methods=['POST'])
def toggle_qr(codigo):
    """Activa/desactiva un código QR"""
    try:
        qr = CodigoQR.query.filter_by(codigo=codigo).first()
        
        if not qr:
            return jsonify({
                'exito': False,
                'mensaje': 'Código QR no encontrado'
            }), 404

        nuevo_estado = qr.toggle_estado()

        return jsonify({
            'exito': True,
            'activo': nuevo_estado,
            'mensaje': f'Código QR {"activado" if nuevo_estado else "desactivado"} exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'exito': False,
            'mensaje': f'Error: {str(e)}'
        }), 500

@api.route('/api/qr/producto/<string:codigo_producto>')
def listar_qrs_producto(codigo_producto):
    """Lista todos los códigos QR de un producto"""
    try:
        qrs = CodigoQR.query.filter_by(
            codigo_producto=codigo_producto
        ).order_by(CodigoQR.fecha_creacion.desc()).all()

        return jsonify([qr.to_dict() for qr in qrs])

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@api.route('/api/qr/imagen/<string:codigo>')
def get_qr_imagen(codigo):
    """Devuelve la imagen de un código QR"""
    try:
        qr = CodigoQR.query.filter_by(codigo=codigo).first()
        
        if not qr:
            return jsonify({
                'error': 'Código QR no encontrado'
            }), 404

        img = qr.generar_imagen_qr()
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/png'
        )

    except Exception as e:
        return jsonify({
            'error': f'Error generando imagen: {str(e)}'
        }), 500

@api.route('/api/qr/download/<string:codigo>')
def download_qr(codigo):
    """Permite descargar la imagen del código QR"""
    try:
        qr = CodigoQR.query.filter_by(codigo=codigo).first()
        
        if not qr:
            return jsonify({
                'error': 'Código QR no encontrado'
            }), 404

        img = qr.generar_imagen_qr()
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr-{codigo}.png'
        )

    except Exception as e:
        return jsonify({
            'error': f'Error descargando imagen: {str(e)}'
        }), 500