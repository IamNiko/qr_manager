from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from config import Config
import os
from extensions import db
from models import Producto
from flask_cors import CORS  # Nuevo: Para permitir conexiones externas
from servicios.gpt import obtener_respuesta_gpt4
from nucleo.estados import gestor_estados
from flask import request, jsonify
from main import manejar_interaccion
from base_datos.sesion import SessionLocal  # Importar la sesión configurada
import logging

# Inicialización de Flask
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Nuevo: Configuración de CORS
CORS(app)

# Configuración de la base de datos
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productos_por_clubes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def crear_tablas_y_datos():
    with app.app_context():
        print("Creando tablas...")
        db.create_all()
        
        print("Verificando si existen datos...")
        if Club.query.count() == 0:
            print("Creando datos iniciales...")
            try:
                # Crear club
                club = Club(
                    codigo_club=Club.generar_codigo(),
                    nombre="Club Test"
                )
                db.session.add(club)
                db.session.flush()  # Para obtener el id_club
                
                # Crear producto
                producto = Producto(
                    codigo_producto=Producto.generar_codigo(club.id_club),
                    id_club=club.id_club,
                    marca="Marca Test",
                    nombre="Producto Test",
                    pvp=100.0,
                    costo=80.0
                )
                db.session.add(producto)
                db.session.flush()
                
                # Crear QR especial
                qr = QREspecial(
                    codigo="UFY43CHGL4JYXL6CXB6U/PROD003003/21/20241115/001",
                    codigo_producto=producto.codigo_producto,
                    credito_disponible=21,
                    fecha_caducidad=datetime.strptime('2024-11-15', '%Y-%m-%d').date(),
                    usos_maximos=10,
                    usos_actuales=0,
                    activo=True
                )
                db.session.add(qr)
                
                db.session.commit()
                print("Datos iniciales creados exitosamente")
                
            except Exception as e:
                print(f"Error creando datos iniciales: {str(e)}")
                db.session.rollback()
                raise e
        else:
            print("Ya existen datos en la base de datos")

# Función de utilidad para generar imagen QR
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
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

# Nuevo: Endpoint para verificar el estado del servidor
@app.route('/api/server/status', methods=['GET'])
def server_status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/qr_especiales/editar/<int:id>', methods=['GET', 'POST'])
def editar_qr_especial(id):
    """Edita un QR especial existente"""
    qr = QREspecial.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Actualizar los valores desde el formulario
            qr.credito_disponible = int(request.form['credito_disponible'])
            qr.fecha_caducidad = datetime.strptime(request.form['fecha_caducidad'], '%Y-%m-%d').date()
            qr.usos_maximos = int(request.form['usos_maximos'])
            
            # Calcular usos_restantes en función de usos_maximos y usos_actuales
            qr.usos_restantes = qr.usos_maximos - qr.usos_actuales
            
            # Guardar cambios en la base de datos
            db.session.commit()
            flash('QR actualizado exitosamente!', 'success')
            return redirect(url_for('listar_qr_especiales'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el QR: {str(e)}', 'error')
    
    return render_template('qr_especiales/editar.html', qr=qr)


@app.route('/qr_especiales')
def listar_qr_especiales():
    """Lista todos los QR especiales generados"""
    qrs = QREspecial.query.order_by(QREspecial.fecha_creacion.desc()).all()
    return render_template('qr_especiales/listar.html', qrs=qrs)

@app.route('/qr_especiales/crear', methods=['GET'])
def crear_qr_especial():
    """Muestra el formulario para crear un nuevo QR especial"""
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template('qr_especiales/crear.html', productos=productos)

@app.route('/api/qr_especial/crear', methods=['POST'])
def api_crear_qr_especial():
    """API endpoint para crear un nuevo QR especial"""
    try:
        data = request.get_json()
        
        # Crear el QR especial
        qr = QREspecial(
            codigo_producto=data['codigo_producto'],
            credito_disponible=int(data['credito_disponible']),  
            fecha_caducidad=datetime.strptime(data['fecha_caducidad'], '%Y-%m-%d').date(),
            usos_maximos=int(data['usos_maximos'])
        )
        
        # Generar el código completo
        qr.codigo = qr.generar_codigo_completo()
        
        db.session.add(qr)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'qr': {
                'codigo': qr.codigo,
                'imagen': f"data:image/png;base64,{qr.get_imagen_base64()}"
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'mensaje': str(e)
        }), 500

@app.route('/api/qr_especial/validar', methods=['POST'])
def api_validar_qr_especial():
    """API endpoint para validar un QR especial"""
    try:
        data = request.get_json()
        qr = QREspecial.query.filter_by(codigo=data['codigo']).first()
        
        if not qr:
            return jsonify({
                'valido': False,
                'mensaje': 'QR no encontrado'
            }), 404
            
        if not qr.es_valido():
            mensaje = 'QR no válido: '
            if qr.esta_caducado():
                mensaje += 'ha caducado'
            elif qr.esta_agotado():
                mensaje += 'se han agotado los usos'
            else:
                mensaje += 'está desactivado'
                
            return jsonify({
                'valido': False,
                'mensaje': mensaje
            }), 400
            
        # Registrar uso
        qr.registrar_uso()
        
        return jsonify({
            'valido': True,
            'producto': qr.producto.to_dict(),
            'credito_disponible': qr.credito_disponible,
            'usos_restantes': qr.usos_maximos - qr.usos_actuales
        })
        
    except Exception as e:
        return jsonify({
            'valido': False,
            'mensaje': str(e)
        }), 500

@app.route('/api/qr_especial/desactivar', methods=['POST'])
def desactivar_qr_especial():
    data = request.get_json()
    codigo = data.get('codigo')

    if not codigo:
        return jsonify({'success': False, 'mensaje': 'Código no proporcionado'}), 400

    qr = QREspecial.query.filter_by(codigo=codigo).first()
    if qr:
        qr.activo = False
        db.session.commit()
        return jsonify({'success': True, 'mensaje': 'QR desactivado exitosamente'}), 200
    else:
        return jsonify({'success': False, 'mensaje': 'QR no encontrado'}), 404


@app.route('/api/qr_especial/activar', methods=['POST'])
def activar_qr_especial():
    data = request.get_json()
    codigo = data.get('codigo')
    
    qr = QREspecial.query.filter_by(codigo=codigo).first()
    
    if not qr:
        return jsonify({'success': False, 'mensaje': 'QR no encontrado'}), 404

    # Activar el QR
    qr.activo = True
    try:
        db.session.commit()
        return jsonify({'success': True, 'mensaje': 'QR activado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error al activar el QR: {str(e)}'}), 500

@app.route('/')
def index():
    """Página principal con estadísticas"""
    stats = {
        'clubes': Club.query.count(),
        'productos': Producto.query.count(),
        'qr_especiales': QREspecial.query.count(),
        'qr_activos': QREspecial.query.filter_by(activo=True).count()
    }
    return render_template('index.html', stats=stats)

# Rutas para Clubes
@app.route('/clubes')
def listar_clubes():
    clubes = Club.query.all()
    return render_template('clubes/listar.html', clubes=clubes)

@app.route('/clubes/crear', methods=['GET', 'POST'])
def crear_club():
    if request.method == 'POST':
        try:
            club = Club(
                codigo_club=Club.generar_codigo(),
                nombre=request.form['nombre']
            )
            db.session.add(club)
            db.session.commit()
            flash('Club creado exitosamente!', 'success')
            return redirect(url_for('listar_clubes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el club: {str(e)}', 'error')
    return render_template('clubes/crear.html')

@app.route('/clubes/editar/<int:id>', methods=['GET', 'POST'])
def editar_club(id):
    club = Club.query.get_or_404(id)
    if request.method == 'POST':
        try:
            club.nombre = request.form['nombre']
            db.session.commit()
            flash('Club actualizado exitosamente!', 'success')
            return redirect(url_for('listar_clubes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el club: {str(e)}', 'error')
    return render_template('clubes/editar.html', club=club)

@app.route('/clubes/eliminar/<int:id>', methods=['POST'])
def eliminar_club(id):
    try:
        club = Club.query.get_or_404(id)
        
        # Eliminar códigos QR asociados a productos del club
        for producto in club.productos:
            CodigoQR.query.filter_by(codigo_producto=producto.codigo_producto).delete()
        
        # Eliminar productos del club
        for producto in club.productos:
            db.session.delete(producto)
            
        # Eliminar el club
        db.session.delete(club)
        db.session.commit()
        
        flash('Club eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el club: {str(e)}', 'error')
    return redirect(url_for('listar_clubes'))

# Rutas para Productos
@app.route('/productos')
def listar_productos():
    productos = Producto.query.join(Club).order_by(Club.nombre, Producto.nombre).all()
    return render_template('productos/listar.html', productos=productos)

@app.route('/productos/crear', methods=['GET', 'POST'])
def crear_producto():
    if request.method == 'POST':
        try:
            producto = Producto(
                codigo_producto=Producto.generar_codigo(request.form['id_club']),
                id_club=request.form['id_club'],
                marca=request.form['marca'],
                nombre=request.form['nombre'],
                pvp=float(request.form['pvp']),
                costo=float(request.form['costo'])
            )
            db.session.add(producto)
            db.session.flush()  # Para obtener el ID del producto

            db.session.commit()
            
            return jsonify({
                'success': True,
                'mensaje': 'Producto creado exitosamente',
                'producto_id': producto.id_producto,
                # 'qr_code': qr_data
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'mensaje': f'Error al crear el producto: {str(e)}'
            }), 500

    clubes = Club.query.all()
    return render_template('productos/crear.html', clubes=clubes)

@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        # Actualizar campos
        producto.pvp = request.form['pvp']
        # # producto.fecha_caducidad = request.form['fecha_caducidad']
        # producto.usos_maximos = request.form['usos_maximos']
        producto.marca = request.form['marca']
        producto.nombre = request.form['nombre']
        producto.pvp = float(request.form['pvp'])
        producto.costo = float(request.form['costo'])
        
        try:
            db.session.commit()
            flash('Producto actualizado exitosamente!', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'error')

    return render_template('productos/editar.html', producto=producto)


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Recurso no encontrado'
        }), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500
    return render_template('500.html'), 500

@app.route('/productos/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}', 'error')
    return redirect(url_for('listar_productos'))


# Rutas para Consultas
@app.route('/consultas')
def consultas():
    return render_template('consultas/index.html')

@app.route('/api/consultar', methods=['POST'])
def consultar():
    try:
        tipo_consulta = request.form['tipo']
        if tipo_consulta == 'productos_club':
            productos = Producto.query.filter_by(id_club=request.form['id_club']).all()
        elif tipo_consulta == 'productos_marca':
            productos = Producto.query.filter(
                Producto.marca.ilike(f"%{request.form['marca']}%")
            ).all()
        elif tipo_consulta == 'rango_pvp':
            productos = Producto.query.filter(
                Producto.pvp.between(
                    float(request.form['min_pvp']),
                    float(request.form['max_pvp'])
                )
            ).all()
        else:
            return jsonify({'error': 'Tipo de consulta no válido'})
        
        return jsonify([producto.to_dict() for producto in productos])
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/clubes')
def get_clubes():
    try:
        clubes = Club.query.all()
        return jsonify([club.to_dict() for club in clubes])
    except Exception as e:
        return jsonify({'error': str(e)})

# Rutas específicas para QR
@app.route('/productos/<int:id>/qr/nuevo', methods=['POST'])
def crear_qr_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        
        qr = CodigoQR(
            codigo=CodigoQR.generar_codigo(producto.codigo_producto),
            codigo_producto=producto.codigo_producto
        )
        db.session.add(qr)
        db.session.commit()
        
        flash('Código QR generado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al generar el código QR: {str(e)}', 'error')
    
    return redirect(url_for('editar_producto', id=id))

@app.route('/productos/qr/<string:codigo>/toggle', methods=['POST'])
def toggle_qr(codigo):
    try:
        qr = CodigoQR.query.filter_by(codigo=codigo).first_or_404()
        nuevo_estado = qr.toggle_estado()
        
        return jsonify({
            'success': True,
            'activo': nuevo_estado,
            'mensaje': f'Código QR {"activado" if nuevo_estado else "desactivado"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'mensaje': f'Error: {str(e)}'
        }), 500

@app.route('/productos/<int:id>/qr')
def detalle_qr_producto(id):
    producto = Producto.query.get_or_404(id)
    return render_template('productos/detalle_qr.html', producto=producto)

# Manejadores de error
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Nuevo: Endpoints para conexión con dispositivos externos
@app.route('/api/external/validate', methods=['POST'])
def validate_external():
    """Endpoint para validación desde dispositivos externos"""
    try:
        data = request.get_json()
        if not data or 'qr_code' not in data:
            return jsonify({
                'success': False,
                'message': 'Código QR no proporcionado'
            }), 400

        # Reutilizar la lógica de validación existente
        qr = QREspecial.query.filter_by(codigo=data['qr_code']).first()
        if not qr:
            return jsonify({
                'success': False,
                'message': 'QR no encontrado'
            }), 404

        return jsonify({
            'success': True,
            'valid': qr.es_valido(),
            'data': qr.to_dict() if qr.es_valido() else None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
@app.template_filter('nombre_club')
def obtener_nombre_club(id_club):
    club = Club.query.get(id_club)
    return club.nombre if club else 'Sin club'

@app.before_request
def log_request():
    print(f"\n=== Nueva petición ===")
    print(f"Ruta: {request.path}")
    print(f"Método: {request.method}")
    print(f"Datos: {request.get_json(silent=True)}")
    print("======================")

# Importar y registrar blueprints
from api.qr_validator import qr_bp
app.register_blueprint(qr_bp, url_prefix='/api')

# Importar modelos después de inicializar db
from models.club import Club
from models.producto import Producto
from models.qr_code import CodigoQR
from models.qr_especial import QREspecial

if __name__ == '__main__':
    print("Iniciando aplicación...")
    crear_tablas_y_datos()
    print("\n=== Rutas registradas ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
    app.run(host='0.0.0.0', port=3000, debug=True)

#endpoint chat

@app.route('/chat')
def chat():
    """Página del chat de soporte"""
    return render_template('chat.html')


logging.basicConfig(level=logging.DEBUG)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Maneja las interacciones del chat con OpenAI"""
    try:
        data = request.get_json()
        mensaje_usuario = data.get('mensaje', '')
        remitente = "web_user"  # Identificador único para usuarios web

        logging.debug(f"Mensaje recibido: {mensaje_usuario}")

        # Crear una nueva sesión de base de datos
        db = SessionLocal()
        try:
            # Llama a la función manejar_interaccion con la sesión
            respuesta = manejar_interaccion(remitente, mensaje_usuario, db=db)
            logging.debug(f"Respuesta generada: {respuesta}")
            return jsonify(respuesta)
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error en el endpoint /api/chat: {str(e)}")
        return jsonify({"respuesta": f"Error: {str(e)}"}), 500

