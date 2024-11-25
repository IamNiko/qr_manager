# QR Manager - Sistema de Gestión para Máquinas Vending

## 📋 Descripción
QR Manager es un sistema integrado basado en Arduino que permite la gestión y validación de códigos QR para máquinas expendedoras (vending). El sistema verifica la autenticidad de los códigos, gestiona créditos y controla las transacciones en tiempo real.

## 🚀 Características Principales
- Lectura de códigos QR mediante módulo integrado
- Validación en tiempo real contra servidor
- Verificación de:
  - Autenticidad del código
  - Fecha de caducidad
  - Cantidad de usos restantes
  - Crédito disponible
- Simulación de transacciones vía monitor serial
- Gestión automática de dispensación de productos
- Actualización automática de base de datos post-transacción

## 🛠️ Tecnologías Utilizadas
- Arduino (Hardware principal)
- Python
- SQLlite
- Flask
- HTML - CSS - JS
- Módulo lector QR
- Servidor de validación
- Base de datos para gestión de códigos y créditos
- Comunicación Serial

## 📊 Flujo de Trabajo
1. **Escaneo**: El usuario presenta el código QR
2. **Validación**: El sistema conecta con el servidor para verificar:
   - Validez del código
   - Estado de caducidad
   - Usos disponibles
   - Saldo
3. **Transacción**:
   - Simulación de importe vía monitor serial
   - Verificación de saldo suficiente
4. **Dispensación**:
   - Simulación de entrega del producto
   - Actualización de la base de datos
   - Registro de la transacción

## 💻 Requisitos del Sistema
- Placa Arduino compatible
- Módulo lector QR
- Conexión a servidor de validación
- Monitor serial para debug y simulación

## 🔧 Instalación
1. Conectar el hardware según el esquema proporcionado
2. Cargar el firmware en la placa Arduino
3. Configurar la conexión con el servidor
4. Verificar la comunicación serial

## 📝 Uso
1. Iniciar el sistema
2. Presentar un código QR válido al lector
3. Esperar la validación del servidor
4. Seguir las instrucciones en el monitor serial
5. Confirmar la transacción

## 🤝 Contribuir
Si deseas contribuir al proyecto:
1. Haz un Fork del repositorio
2. Crea una rama para tu característica 
3. Commit tus cambios 
4. Push a la rama 
5. Abre un Pull Request

## ⚠️ Estado del Proyecto
Desarrollo primera version.

## 📄 Licencia
Sin licencia.

## 👥 Autores
- Nicolas Gentile Rosello

## 📞 Contacto
- nicolasgentilepro@gmail.com

## 🙏 Agradecimientos
- Arduino PKAP Sports 
