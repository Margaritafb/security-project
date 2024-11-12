#include <Arduino.h>
//HardwareSerial Serial1(1); // Usar UART1
// SensorData.h
class SensorData {
private:
    uint8_t id;
    uint8_t day;
    uint8_t month;
    uint8_t year;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
    uint8_t state;
    bool updated;

public:
    SensorData() : id(0), updated(false) {}

    void updateData(uint8_t id, uint8_t day, uint8_t month, uint8_t year,
                   uint8_t hour, uint8_t minute, uint8_t second, uint8_t state) {
        this->id = id;
        this->day = day;
        this->month = month;
        this->year = year;
        this->hour = hour;
        this->minute = minute;
        this->second = second;
        this->state = state;
        this->updated = true;
    }

    uint8_t getId() const { return id; }
    uint8_t getState() const { return state; }
    bool isUpdated() const { return updated; }
    
    void printInfo() const {
        //Serial.printf("Sensor %d actualizado: Estado=%d, Fecha=%02d/%02d/%02d, Hora=%02d:%02d:%02d\n",
        //             id, state, day, month, year, hour, minute, second);
    }
};

// MessageParser.h
class MessageParser {
private:
    static const uint8_t MESSAGE_LENGTH = 9;
    uint8_t buffer[MESSAGE_LENGTH];
    int dataIndex;

    uint8_t calculateChecksum(const uint8_t* data, int length) const {
        uint8_t sum = 0;
        for (int i = 0; i < length - 1; i++) {
            sum += data[i];
        }
        return sum;
    }

public:
    MessageParser() : dataIndex(0) {}

    bool addByte(uint8_t byte) {
        if (dataIndex < MESSAGE_LENGTH) {
            buffer[dataIndex++] = byte;
            return dataIndex == MESSAGE_LENGTH;
        }
        return false;
    }

    bool isChecksumValid() const {
        return calculateChecksum(buffer, MESSAGE_LENGTH) == buffer[MESSAGE_LENGTH - 1];
    }

    void reset() {
        dataIndex = 0;
    }

    uint8_t getSensorId() const { return buffer[0]; }
    uint8_t* getData() { return buffer; }
};

// LEDController.h
class LEDController {
private:
    const uint8_t pin;
    
public:
    LEDController(uint8_t pin) : pin(pin) {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW);
    }

    void update(const SensorData& sensor1, const SensorData& sensor2) {
        if (sensor1.isUpdated() && sensor2.isUpdated()) {
            // Modifica esta lógica según tus necesidades
            if (sensor1.getState() == 1 && sensor2.getState() == 1) {
                digitalWrite(pin, HIGH);
            } else {
                digitalWrite(pin, LOW);
            }
        }
    }
};

// SensorManager.h
class SensorManager {
private:
    const uint8_t sensor1Id;
    const uint8_t sensor2Id;
    SensorData sensor1;
    SensorData sensor2;
    LEDController& ledController;
    MessageParser parser;

public:
    SensorManager(uint8_t s1Id, uint8_t s2Id, LEDController& led) 
        : sensor1Id(s1Id), sensor2Id(s2Id), ledController(led) {}

    void processSerialData() {
        while (Serial.available() > 0) {
            uint8_t receivedByte = Serial.read();
            //Serial.print("Byte recibido: ");
            //Serial.println(receivedByte, HEX);  // Mostrar el byte recibido en el monitor serial
            if (parser.addByte(receivedByte)) {
                processMessage();
                parser.reset();
            }
        }
    }

private:
    void processMessage() {
    if (!parser.isChecksumValid()) {
        //Serial.println("Error de checksum");
        return;
    }

    uint8_t* data = parser.getData();
    uint8_t sensorId = parser.getSensorId();
    //Serial.print("Mensaje recibido del sensor: ");
    //Serial.println(sensorId);

    if (sensorId == sensor1Id || sensorId == sensor2Id) {
        //Serial.println("Actualizando sensor...");
        SensorData& currentSensor = (sensorId == sensor1Id) ? sensor1 : sensor2;

        // Actualizar los datos del sensor
        currentSensor.updateData(
            sensorId,
            data[1], // day
            data[2], // month
            data[3], // year
            data[4], // hour
            data[5], // minute
            data[6], // second
            data[7]  // state
        );

        currentSensor.printInfo();  // Imprimir los datos del sensor

        // Actualizar el LED basado en el estado de los sensores
        ledController.update(sensor1, sensor2);
    }
}
};

// Main program
#define LED_PIN 2
#define SENSOR1_ID 1
#define SENSOR2_ID 2

LEDController ledController(LED_PIN);
SensorManager sensorManager(SENSOR1_ID, SENSOR2_ID, ledController);

void setup() {
    Serial.begin(115200);  // Para monitoreo en el PC
    //Serial1.begin(115200, SERIAL_8N1, 16, 17);  // Usar GPIO 16 para RX y GPIO 17 para TX
    //Serial.println("Iniciando ESP32...");
}


void loop() {
    // Leer datos del puerto Serial1
    /*if (Serial1.available()) {
        uint8_t receivedByte = Serial1.read();
        Serial.print("Byte recibido: ");
        Serial.println(receivedByte, HEX);  // Mostrar el byte recibido en el monitor serial
        // Procesar el byte recibido
        
    }*/
    sensorManager.processSerialData();
    //Serial.println("Ciclo del loop finalizado");
    //delay(1000);  // Añadir un pequeño delay para evitar que el monitor se sature
}