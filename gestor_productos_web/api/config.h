#ifndef CONFIG_H
#define CONFIG_H

// Configuración WiFi
#define WIFI_SSID "400guest"
#define WIFI_PASSWORD "airbnb400"

// Configuración del servidor
#define SERVER_HOST "192.168.1.XXX"  // Cambia esto por la IP de tu servidor local
#define SERVER_PORT 5000             // Puerto por defecto de Flask
#define API_ENDPOINT "/api/validar_qr"  // Endpoint para validación

// Configuración de Hardware
#define LED_PIN 2           // Pin para LED de estado
#define BUZZER_PIN 4        // Pin para buzzer (opcional)
#define QR_READER_BAUDRATE 9600  // Velocidad del lector QR

// Timeouts y delays
#define WIFI_TIMEOUT 20000       // Timeout para conexión WiFi (ms)
#define REQUEST_TIMEOUT 5000     // Timeout para peticiones HTTP (ms)
#define SCAN_DELAY 1000         // Delay entre escaneos (ms)

// Indicadores LED
#define LED_CONNECTING 100    // Parpadeo rápido mientras conecta
#define LED_CONNECTED 1000    // Parpadeo lento cuando está conectado
#define LED_ERROR 2000        // Parpadeo muy lento en error

#endif