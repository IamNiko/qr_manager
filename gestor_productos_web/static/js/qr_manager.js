class QRManager {
    constructor() {
        this.baseUrl = '/api';
    }

    // Crear nuevo código QR
    async crearQR(codigoProducto) {
        try {
            const response = await fetch(`${this.baseUrl}/qr/crear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ codigo_producto: codigoProducto })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.mensaje);
            }

            this.mostrarMensaje(data.mensaje, 'success');
            return data.qr;
        } catch (error) {
            this.mostrarMensaje(error.message, 'error');
            return null;
        }
    }

    // Cambiar estado de un QR (activar/desactivar)
    async toggleQR(codigoQR) {
        try {
            const response = await fetch(`${this.baseUrl}/qr/${codigoQR}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.mensaje);
            }

            this.mostrarMensaje(data.mensaje, 'success');
            return data.activo;
        } catch (error) {
            this.mostrarMensaje(error.message, 'error');
            return null;
        }
    }

    // Obtener QRs de un producto
    async obtenerQRsProducto(codigoProducto) {
        try {
            const response = await fetch(`${this.baseUrl}/qr/producto/${codigoProducto}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.mensaje);
            }

            return data;
        } catch (error) {
            this.mostrarMensaje(error.message, 'error');
            return [];
        }
    }

    // Validar un código QR
    async validarQR(codigoQR) {
        try {
            const response = await fetch(`${this.baseUrl}/validar_qr`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ codigo_qr: codigoQR })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.mensaje);
            }

            return data;
        } catch (error) {
            this.mostrarMensaje(error.message, 'error');
            return null;
        }
    }

    // Actualizar interfaz de QRs
    actualizarListaQRs(codigoProducto) {
        const container = document.getElementById('qr-list');
        if (!container) return;

        this.obtenerQRsProducto(codigoProducto).then(qrs => {
            container.innerHTML = qrs.map(qr => this.crearQRCard(qr)).join('');
            this.agregarEventosQR();
        });
    }

    // Crear HTML para una tarjeta de QR
    crearQRCard(qr) {
        return `
            <div class="qr-card qr-fade-in" data-qr="${qr.codigo}">
                <div class="qr-card-header">
                    <span class="qr-status ${qr.activo ? 'active' : 'inactive'}">
                        ${qr.activo ? 'Activo' : 'Inactivo'}
                    </span>
                    <small>${new Date(qr.fecha_creacion).toLocaleDateString()}</small>
                </div>
                <div class="qr-card-body">
                    <div class="qr-code">
                        <!-- Aquí iría la imagen del QR -->
                        <img src="/api/qr/imagen/${qr.codigo}" alt="QR Code">
                    </div>
                    <div class="qr-details">
                        <p>Código: ${qr.codigo}</p>
                        ${qr.ultimo_uso ? 
                            `<p>Último uso: ${new Date(qr.ultimo_uso).toLocaleString()}</p>` : 
                            '<p>Sin uso</p>'}
                    </div>
                </div>
                <div class="qr-card-footer">
                    <div class="qr-actions">
                        <button class="btn btn-warning toggle-qr" data-qr="${qr.codigo}">
                            ${qr.activo ? 'Desactivar' : 'Activar'}
                        </button>
                        <button class="btn btn-primary download-qr" data-qr="${qr.codigo}">
                            Descargar
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Agregar eventos a los botones de QR
    agregarEventosQR() {
        document.querySelectorAll('.toggle-qr').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const codigoQR = e.target.dataset.qr;
                this.toggleQR(codigoQR).then(() => {
                    this.actualizarListaQRs(codigoQR.split('-')[1]); // Asumiendo formato QR-PRODXXX
                });
            });
        });

        document.querySelectorAll('.download-qr').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const codigoQR = e.target.dataset.qr;
                window.open(`/api/qr/download/${codigoQR}`, '_blank');
            });
        });
    }

    // Mostrar mensajes al usuario
    mostrarMensaje(mensaje, tipo) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : 'success'} qr-fade-in`;
        alertDiv.textContent = mensaje;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}

// Inicializar el administrador de QR cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.qrManager = new QRManager();
});