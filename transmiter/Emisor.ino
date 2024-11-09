#include <message-builder.h>
#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "TEDDY_PLUS";
const char* password = "71588678";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_topic = "esp32/buttons";

WiFiClient espClient;
PubSubClient client(espClient);

const int button1 = 4;
const int button2 = 16;
const int button3 = 17;
int b1 = 0;
int b2 = 0;
int b3 = 0;

unsigned long lastReconnectAttempt = 0;
const long reconnectInterval = 5000;

void initNetwork() {
  delay(10);
  Serial.println("Conectando a WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi conectado");
  Serial.println("Dirección IP: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  initNetwork();

  if (WiFi.status() == WL_CONNECTED) {
    client.setServer(mqtt_server, mqtt_port);
    Serial.println("Servidor MQTT configurado");
  }

  pinMode(button1, INPUT_PULLUP);
  pinMode(button2, INPUT_PULLUP);
  pinMode(button3, INPUT_PULLUP);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      connectToMQTT();
    }
    client.loop();

    b1 = digitalRead(button1);
    b2 = digitalRead(button2);
    b3 = digitalRead(button3);

    byte msg[9];
    buildMessage(msg, 1, b1, millis());
    publishMessage(msg, 9);
    buildMessage(msg, 2, b2, millis());
    publishMessage(msg, 9);
    buildMessage(msg, 3, b3, millis());
    publishMessage(msg, 9);
    for (int i = 0; i < 9; i++) {
      Serial.print(msg[i], HEX);  // Imprime en formato hexadecimal
    }

    delay(5000);
  } else {
    Serial.println("Reintentando conexión WiFi...");
    initNetwork();
    delay(5000);
  }
}

void connectToMQTT() {
  if (client.connect("ESP32Client")) {
    Serial.println("Conectado a MQTT");
  } else {
    Serial.print("Fallo MQTT, estado=");
    Serial.println(client.state());
  }
}

void publishMessage(byte* message, int len) {
  if (!client.connected()) {
    Serial.println("MQTT desconectado, no se puede publicar");
    return;
  }

  bool success = client.publish(mqtt_topic, message, len);
  if (success) {
    Serial.println("Mensaje publicado con éxito");
  } else {
    Serial.println("Error al publicar mensaje");
  }
}
