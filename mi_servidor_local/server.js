// Conectar a la base de datos SQLite
// const dbPath = "C:/Users/nicol/QR_PROJ - CASHDUINO/gestor_productos_web/instance/productos_por_clubes.db";

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const port = 3000;

// Conectar a la base de datos SQLite
const dbPath = "C:/Users/nicol/QR_PROJ - CASHDUINO/gestor_productos_web/instance/productos_por_clubes.db";
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error("Error al conectar con la base de datos:", err.message);
    } else {
        console.log("Conectado a la base de datos SQLite.");
    }
});

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Ruta para validar QR con doble validación
app.post('/api/validar_qr', (req, res) => {
    const { codigo_qr, segundaValidacion, importe } = req.body;

    if (!codigo_qr) {
        return res.json({
            valido: false,
            mensaje: 'Código QR no proporcionado'
        });
    }

    // Consulta para obtener información del QR y producto
    const query = `SELECT qr.*, p.nombre, p.marca, p.pvp as pvp 
                  FROM qr_especiales qr 
                  JOIN productos p ON qr.codigo_producto = p.codigo_producto 
                  WHERE qr.codigo = ?`;

    db.get(query, [codigo_qr], (err, row) => {
        if (err) {
            console.error("Error en la consulta:", err.message);
            return res.status(500).json({ 
                valido: false, 
                mensaje: 'Error del servidor' 
            });
        }

        if (!row) {
            return res.json({
                valido: false,
                mensaje: "QR inválido o no encontrado"
            });
        }

        // Verificar usos restantes
        if (row.usos_restantes <= 0) {
            return res.json({
                valido: false,
                mensaje: "Código QR agotado"
            });
        }

        if (segundaValidacion) {
            // Segunda validación: verificar si el crédito es suficiente
            const importeFloat = parseFloat(importe);
            if (importeFloat > row.credito_disponible) {
                return res.json({
                    valido: false,
                    mensaje: "Crédito insuficiente",
                    credito: row.credito_disponible,
                    producto: {
                        nombre: row.nombre,
                        marca: row.marca,
                        pvp: row.pvp,
                        credito_disponible: row.credito_disponible
                    }
                });
            }

            // Si el crédito es suficiente, actualizar usos y credito_disponible
            const nuevosUsosRestantes = row.usos_restantes - 1;
            const nuevosUsosActuales = row.usos_actuales + 1;
            const nuevoPrecioEspecial = row.credito_disponible - importeFloat;

            const updateQuery = `UPDATE qr_especiales 
                               SET usos_restantes = ?, 
                                   usos_actuales = ?,
                                   credito_disponible = ? 
                               WHERE codigo = ?`;

            db.run(updateQuery, [nuevosUsosRestantes, nuevosUsosActuales, nuevoPrecioEspecial, codigo_qr], (err) => {
                if (err) {
                    console.error("Error al actualizar datos:", err.message);
                    return res.status(500).json({ 
                        valido: false, 
                        mensaje: 'Error al actualizar los datos' 
                    });
                }

                console.log(`Actualización exitosa:
                    - Usos restantes: ${nuevosUsosRestantes}
                    - Usos actuales: ${nuevosUsosActuales}
                    - Nuevo saldo: ${nuevoPrecioEspecial}
                    - Importe usado: ${importeFloat}`);

                res.json({
                    valido: true,
                    mensaje: "CREDITO DISPONIBLE",
                    credito: nuevoPrecioEspecial,
                    importe_usado: importeFloat,
                    producto: {
                        nombre: row.nombre,
                        marca: row.marca,
                        pvp_normal: row.pvp,
                        credito_disponible: nuevoPrecioEspecial
                    },
                    usos_restantes: nuevosUsosRestantes,
                    usos_actuales: nuevosUsosActuales
                });
            });
        } else {
            // Primera validación: solo verificar validez
            res.json({
                valido: true,
                mensaje: "CÓDIGO VÁLIDO",
                producto: {
                    nombre: row.nombre,
                    marca: row.marca,
                    pvp: row.pvp,
                    credito_disponible: row.credito_disponible
                },
                usos_restantes: row.usos_restantes,
                usos_actuales: row.usos_actuales,
                solicitud_importe: true
            });
        }
    });
});

app.listen(port, () => {
    console.log(`Servidor corriendo en http://localhost:${port}`);
});