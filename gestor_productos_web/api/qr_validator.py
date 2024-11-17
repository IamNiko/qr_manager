from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import sqlite3
from functools import wraps
from io import BytesIO
import qrcode
import base64
from flask import Flask
from flask_cors import CORS  # Nuevo: Agregamos CORS para el blueprint

qr_bp = Blueprint('qr', __name__)
CORS(qr_bp)  # Nuevo: Habilitamos CORS para todas las rutas de la API

def get_db_connection():
    conn = sqlite3.connect('productos_por_clubes.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_qr_base64(text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Nuevo: Endpoint para verificar estado de la API
@qr_bp.route('/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })

@qr_bp.route('/validar_qr', methods=['POST'])
def validar_qr():
    print("\n=== INICIO VALIDACIÓN QR (qr_validator.py) ===")
    conn = get_db_connection()
    try:
        data = request.get_json()
        print(f"Datos recibidos: {data}")
        
        if not data or 'codigo_qr' not in data:
            print("Error: No se proporcionó código QR")
            return jsonify({
                'valido': False,
                'mensaje': 'Código QR no proporcionado'
            }), 400

        codigo_qr = data['codigo_qr']
        print(f"Validando QR: {codigo_qr}")
        
        # Verificar la conexión a la base de datos
        print("Verificando tablas en la base de datos...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        print("Tablas encontradas:", [tabla[0] for tabla in tablas])
        
        # Verificar si hay datos en las tablas
        print("\nVerificando datos en las tablas:")
        for tabla in tablas:
            if tabla[0] not in ['sqlite_sequence']:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
                count = cursor.fetchone()[0]
                print(f"Tabla {tabla[0]}: {count} registros")
        
        # Ejecutar la consulta original con más logging
        query = '''
            SELECT   
                qr.activo,
                qr.credito_disponible,
                qr.usos_maximos,
                qr.usos_actuales,
                qr.fecha_caducidad,
                p.codigo_producto,
                p.marca,
                p.nombre,
                p.pvp as precio_normal,
                c.nombre as nombre_club
            FROM qr_especiales qr
            JOIN productos p ON qr.codigo_producto = p.codigo_producto
            JOIN clubes c ON p.id_club = c.id_club
            WHERE qr.codigo = ?
        '''
        print(f"\nEjecutando consulta SQL:")
        print("Query:", query)
        print("Parámetro:", codigo_qr)
        
        cursor.execute(query, (codigo_qr,))
        result = cursor.fetchone()
        
        if result:
            print("\nResultado encontrado:")
            print(dict(result))
        else:
            print("\nNo se encontraron resultados")
            return jsonify({
                'valido': False,
                'mensaje': 'Código QR no encontrado'
            }), 404

        # Verificar si está activo
        if not result['activo']:
            print("QR inactivo")
            return jsonify({
                'valido': False,
                'mensaje': 'Código QR inactivo'
            }), 403

        # Resto del código igual...

    except Exception as e:
        print(f"Error en validación: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        print("Traceback completo:")
        print(traceback.format_exc())
        return jsonify({
            'valido': False,
            'mensaje': f'Error: {str(e)}'
        }), 500
    finally:
        print("\nCerrando conexión a la base de datos")
        conn.close()
        print("=== FIN PRIMERA VALIDACIÓN QR ===\n")
        
@qr_bp.route('/api/qr/producto/<string:codigo_producto>')
def get_qr_producto(codigo_producto):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id_qr, codigo, activo, fecha_creacion, ultimo_uso
            FROM codigos_qr
            WHERE codigo_producto = ?
            ORDER BY fecha_creacion DESC
        ''', (codigo_producto,))
        
        qrs = []
        for qr in cursor.fetchall():
            qr_dict = dict(qr)
            qr_dict['imagen'] = generate_qr_base64(qr['codigo'])
            qrs.append(qr_dict)
            
        return jsonify(qrs)

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
    finally:
        conn.close()

@qr_bp.route('/api/qr/imagen/<string:codigo>')
def get_qr_imagen(codigo):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({
            'error': f'Error generando imagen: {str(e)}'
        }), 500

@qr_bp.route('/api/qr/download/<string:codigo>')
def download_qr(codigo):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
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

# Los error handlers se mueven al blueprint
@qr_bp.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Recurso no encontrado'
        }), 404
    return jsonify({
        'error': 'Página no encontrada'
    }), 404

@qr_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Error interno del servidor'
    }), 500