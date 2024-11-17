#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <SoftwareSerial.h>
#include <LiquidCrystal.h>

// Configuración de WiFi
const char* ssid = "400guest";
const char* password = "airbnb400";

// Configuración del servidor
const char* serverAddress = "10.0.0.64";
const int serverPort = 3000;

// Pines para LEDs
const int LED_VERDE = 2;
const int LED_ROJO = 3;

// Pines para el lector QR (UART)
const int QR_RX = 0;
const int QR_TX = 1;

// Pines para LCD 1602
const int LCD_RS = 8;
const int LCD_E = 9;
const int LCD_D4 = 4;
const int LCD_D5 = 5;
const int LCD_D6 = 6;
const int LCD_D7 = 7;

// Estados del sistema
enum Estado {
  ESPERANDO_QR,
  ESPERANDO_IMPORTE,
  ESPERANDO_SEGUNDA_VALIDACION
};

// Variables de estado y control
Estado estadoActual = ESPERANDO_QR;
String ultimoQR = "";
String importeActual = "";
unsigned long tiempoUltimaLectura = 0;
unsigned long tiempoUltimaAccion = 0;
const unsigned long TIEMPO_ENTRE_LECTURAS = 3000;
const unsigned long TIMEOUT_IMPORTE = 30000;    // 30 segundos para ingresar importe
const unsigned long TIMEOUT_SEGUNDA_VALIDACION = 60000;  // 1 minuto para segunda validación

// Inicializar LCD
LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// Inicializar puerto serial para el lector QR
SoftwareSerial qrReader(QR_RX, QR_TX);

// Cliente WiFi
WiFiClient wifi;
HttpClient client = HttpClient(wifi, serverAddress, serverPort);

void setup() {
  Serial.begin(9600);
  
  // Inicializar LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("Iniciando");
  lcd.setCursor(0, 1);
  lcd.print("Sistema QR...");
  
  qrReader.begin(9600);
  
  // Configurar LEDs
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);
  
  // Test inicial de LEDs
  digitalWrite(LED_VERDE, HIGH);
  digitalWrite(LED_ROJO, HIGH);
  delay(1000);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, LOW);
  
  // Conectar a WiFi
  conectarWiFi();
  
  mostrarPantallaEspera();
}

void conectarWiFi() {
  lcd.clear();
  lcd.print("Conectando a");
  lcd.setCursor(0, 1);
  lcd.print("WiFi: " + String(ssid));
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  
  lcd.clear();
  lcd.print("WiFi Conectado!");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());
  delay(2000);
}

void mostrarPantallaEspera() {
  lcd.clear();
  switch(estadoActual) {
    case ESPERANDO_QR:
      lcd.print("Escanee QR");
      lcd.setCursor(0, 1);
      lcd.print("para validar");
      break;
    case ESPERANDO_IMPORTE:
      lcd.print("Esperando importe");
      lcd.setCursor(0, 1);
      lcd.print("via Serial");
      break;
    case ESPERANDO_SEGUNDA_VALIDACION:
      lcd.print("Escanee QR para");
      lcd.setCursor(0, 1);
      lcd.print("confirmar: $" + importeActual);
      break;
  }
}

void validateQRCode(String qrCode) {
  Serial.println("\n=== INICIO VALIDACIÓN QR ===");
  Serial.print("Estado actual: ");
  switch(estadoActual) {
    case ESPERANDO_QR:
      Serial.println("ESPERANDO_QR");
      break;
    case ESPERANDO_IMPORTE:
      Serial.println("ESPERANDO_IMPORTE");
      break;
    case ESPERANDO_SEGUNDA_VALIDACION:
      Serial.println("ESPERANDO_SEGUNDA_VALIDACION");
      break;
  }
  
  if (qrCode == ultimoQR && 
      (millis() - tiempoUltimaLectura) < TIEMPO_ENTRE_LECTURAS) {
    Serial.println("Lectura duplicada ignorada");
    return;
  }
  
  lcd.clear();
  lcd.print("Validando QR...");
  
  StaticJsonDocument<200> doc;
  doc["codigo_qr"] = qrCode;
  
  if (estadoActual == ESPERANDO_SEGUNDA_VALIDACION) {
    doc["segundaValidacion"] = true;
    doc["importe"] = importeActual.toFloat();
    Serial.println("Segunda validación - Importe: $" + importeActual);
  }
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Enviando petición al servidor...");
  Serial.println("Datos: " + jsonString);
  
  client.beginRequest();
  client.post("/api/validar_qr");
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", jsonString.length());
  client.beginBody();
  client.print(jsonString);
  client.endRequest();
  
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();
  
  Serial.println("Código de estado: " + String(statusCode));
  Serial.println("Respuesta: " + response);
  
  if (statusCode == 200) {
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      bool valido = responseDoc["valido"];
      Serial.println("QR válido: " + String(valido ? "SI" : "NO"));
      
      lcd.clear();
      if (valido) {
        digitalWrite(LED_VERDE, HIGH);
        digitalWrite(LED_ROJO, LOW);
        
        if (estadoActual == ESPERANDO_QR) {
          Serial.println("Primera validación exitosa - Cambiando a ESPERANDO_IMPORTE");
          Serial.println("\nIngrese el importe por el monitor serial y presione Enter");
          Serial.println("Formato: 123.45");
          
          lcd.print("QR Valido!");
          lcd.setCursor(0, 1);
          lcd.print("Espere importe..");
          delay(2000);
          estadoActual = ESPERANDO_IMPORTE;
          importeActual = "";
          tiempoUltimaAccion = millis();  // Iniciar contador de timeout
        }
        else if (estadoActual == ESPERANDO_SEGUNDA_VALIDACION) {
          float credito = responseDoc["credito"];
          float importeFloat = importeActual.toFloat();
          
          Serial.println("Segunda validación - Crédito: $" + String(credito));
          Serial.println("Importe solicitado: $" + String(importeFloat));
          
          if (credito >= importeFloat) {
            lcd.print("Credito OK");
            lcd.setCursor(0, 1);
            lcd.print("Dispensando...");
            delay(3000);
          } else {
            lcd.print("Credito insuf.");
            lcd.setCursor(0, 1);
            lcd.print("Saldo: $" + String(credito));
            delay(3000);
          }
          
          estadoActual = ESPERANDO_QR;
          importeActual = "";
        }
      } else {
        digitalWrite(LED_VERDE, LOW);
        digitalWrite(LED_ROJO, HIGH);
        const char* mensaje = responseDoc["mensaje"];
        lcd.print("QR Invalido");
        lcd.setCursor(0, 1);
        lcd.print(mensaje);
        estadoActual = ESPERANDO_QR;
        delay(3000);
      }
    } else {
      Serial.println("Error deserializando respuesta: " + String(error.c_str()));
      lcd.clear();
      lcd.print("Error de lectura");
      lcd.setCursor(0, 1);
      lcd.print("Intente de nuevo");
      estadoActual = ESPERANDO_QR;
      delay(3000);
    }
  } else {
    lcd.clear();
    lcd.print("Error Servidor");
    lcd.setCursor(0, 1);
    lcd.print("Codigo: " + String(statusCode));
    estadoActual = ESPERANDO_QR;
    delay(3000);
  }
  
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, LOW);
  mostrarPantallaEspera();
  
  ultimoQR = qrCode;
  tiempoUltimaLectura = millis();
  
  Serial.println("=== FIN VALIDACIÓN QR ===\n");
}

void checkWiFiStatus() {
  if (WiFi.status() != WL_CONNECTED) {
    lcd.clear();
    lcd.print("WiFi Perdido!");
    lcd.setCursor(0, 1);
    lcd.print("Reconectando...");
    
    conectarWiFi();
  }
}

void checkTimeouts() {
  unsigned long tiempoActual = millis();
  
  if (estadoActual == ESPERANDO_IMPORTE) {
    if (tiempoActual - tiempoUltimaAccion > TIMEOUT_IMPORTE) {
      Serial.println("Timeout esperando importe");
      lcd.clear();
      lcd.print("Tiempo agotado");
      delay(2000);
      estadoActual = ESPERANDO_QR;
      mostrarPantallaEspera();
    }
  }
  else if (estadoActual == ESPERANDO_SEGUNDA_VALIDACION) {
    if (tiempoActual - tiempoUltimaAccion > TIMEOUT_SEGUNDA_VALIDACION) {
      Serial.println("Timeout esperando segunda validación");
      lcd.clear();
      lcd.print("Tiempo agotado");
      delay(2000);
      estadoActual = ESPERANDO_QR;
      mostrarPantallaEspera();
    }
  }
}

void loop() {
  checkWiFiStatus();
  checkTimeouts();
  
  // Manejar entrada serial para el importe
  if (estadoActual == ESPERANDO_IMPORTE && Serial.available()) {
    importeActual = Serial.readStringUntil('\n');
    importeActual.trim();
    
    if (importeActual.length() > 0) {
      Serial.println("Importe ingresado: $" + importeActual);
      estadoActual = ESPERANDO_SEGUNDA_VALIDACION;
      tiempoUltimaAccion = millis();  // Reiniciar contador para segunda validación
      mostrarPantallaEspera();
    }
  }
  
  if (qrReader.available()) {
    String qrCode = qrReader.readStringUntil('\n');
    validateQRCode(qrCode);
  }
  
  if (Serial.available() && estadoActual != ESPERANDO_IMPORTE) {
    String qrCode = Serial.readStringUntil('\n');
    validateQRCode(qrCode);
  }
}