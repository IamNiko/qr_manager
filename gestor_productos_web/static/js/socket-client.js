// static/js/socket-client.js
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('Conectado al servidor');
});

socket.on('qr_update', (data) => {
    console.log('QR escaneado:', data);
    // Aquí puedes agregar lógica para actualizar la UI
});

socket.on('activity_update', (data) => {
    console.log('Actualización de actividad:', data);
    // Aquí puedes agregar lógica para actualizar la UI
});

socket.on('disconnect', () => {
    console.log('Desconectado del servidor');
});

// Función para emitir eventos al servidor
function emitQRScan(qrData) {
    socket.emit('qr_scanned', qrData);
}