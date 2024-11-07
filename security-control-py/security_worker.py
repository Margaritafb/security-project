import logging
import threading
from queue import Queue
import time
from redis import Redis
import json
from paho.mqtt import client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)

# Configuración para Redis y MQTT
REDIS_LATEST_HOST = "redis-latest"
REDIS_LATEST_PORT = 6379
REDIS_HISTORY_HOST = "redis-history"
REDIS_HISTORY_PORT = 6380
MQTT_BROKER = "broker.hivemq.com"  
MQTT_PORT = 1883


class MQTTReader:
    def __init__(self, client: mqtt.Client, topic: str, output_queue: Queue):
        """
        Inicializa el lector MQTT.

        Args:
            client (mqtt.Client): Cliente de MQTT.
            topic (str): Tópico al cual suscribirse.
            output_queue (Queue): Cola para almacenar los mensajes recibidos.
        """
        self.__client = client
        self.__topic = topic
        self._running = False
        self._output_queue = output_queue

    def stop(self):

        self._running = False
        
    def __decode_message(self, message: bytes) -> dict:
        """
        Decodifica un mensaje de 9 bytes recibido por MQTT, incluyendo el cálculo de checksum.

        Args:
            message (bytes): Mensaje en bytes recibido desde el tópico MQTT.

        Returns:
            dict: Diccionario con los datos decodificados del mensaje.

        Raises:
            ValueError: Si el checksum no coincide o el formato es incorrecto.
        """
        
        if len(message) != 9:
            raise ValueError("El mensaje debe tener exactamente 9 bytes.")
    
        # Extraer los campos
        button_id = message[0]
        timestamp = (
            (message[1] << 40) |
            (message[2] << 32) |
            (message[3] << 24) |
            (message[4] << 16) |
            (message[5] << 8) |
            message[6]
        )
        button_state = message[7]
    
        # Calcular y verificar el checksum
        calculated_checksum = sum(message[:8]) & 0xFF
        received_checksum = message[8]
        if calculated_checksum != received_checksum:
            raise ValueError("Checksum no coincide, mensaje corrupto.")
    
        return {
            "sensor_id": button_id,
            "timestamp": timestamp,
            "sensor_state": button_state,
        }


    def process_messages(self, client, userdata, message):
        """
        Callback que procesa cada mensaje recibido en el tópico.

        Args:
            client (mqtt.Client): Cliente de MQTT.
            userdata: Datos del usuario (no utilizado).
            message: Mensaje recibido en el tópico.
        """
        logger = logging.getLogger(__name__)
        payload = message.payload

        # Imprimir el mensaje en bruto
        logger.info(f"Mensaje recibido en bruto: {payload}")
        
        try:
            # Decodificar el mensaje de 9 bytes y colocarlo en la cola
            decoded_message = self.__decode_message(payload)
            self._output_queue.put(decoded_message)
            logger.info(f"Message added to queue: {decoded_message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def runner(self):
        """
        Inicia el lector MQTT y suscripción al tópico.
        """
        logger = logging.getLogger(__name__)
        self._running = True
        self.__client.subscribe(self.__topic)
        self.__client.on_message = self.process_messages
        logger.info("Running MQTT reader")
        self.__client.loop_forever()

class QueueConsumer:
    def __init__(self, input_queue: Queue, redis_latest: Redis, redis_history: Redis):
        """
        Inicializa el consumidor de la cola y el cliente de Redis.

        Args:
            input_queue (Queue): Cola de mensajes que se procesarán.
            redis_client (Redis): Instancia del cliente Redis donde se almacenarán los datos.
        """
        self._input_queue = input_queue
        self._redis_latest = redis_latest
        self._redis_history = redis_history
        self._running = False

    def stop(self):
        self._running = False

    def runner(self):
        logger = logging.getLogger(__name__)
        self._running = True
        logger.info("Running QueueConsumer")

        while self._running:
            if not self._input_queue.empty():
                message = self._input_queue.get()
                sensor_id = message.get("sensor_id")
                timestamp = message.get("timestamp")
                sensor_state = message.get("sensor_state")

                # Datos a almacenar en Redis
                data = {
                    "timestamp": timestamp,
                    "sensor_state": sensor_state
                }

                try:
                    # Almacena solo el último valor en redis-latest
                    self._redis_latest.hset(f"sensor:{sensor_id}", mapping=data)

                    # Almacena cada lectura en redis-history como un historial
                    self._redis_history.rpush(f"sensor:{sensor_id}:history", json.dumps(data))

                    logger.info(f"Stored latest reading for sensor {sensor_id} in redis-latest and history in redis-history.")
                except Exception as e:
                    logger.error(f"Error storing data in Redis: {e}")
            else:
                time.sleep(0.1)  # Espera un momento si la cola está vacía para no consumir CPU innecesariamente

def main():
    """Configura y ejecuta el lector MQTT y el QueueConsumer en hilos diferentes."""

    received_queue = Queue()

    # Conexiones a Redis
    redis_latest = Redis(host=REDIS_LATEST_HOST, port=REDIS_LATEST_PORT, db=0)
    redis_history = Redis(host=REDIS_HISTORY_HOST, port=REDIS_HISTORY_PORT, db=0)

    # Configura MQTT
    client = mqtt.Client()
    client.connect(host=MQTT_BROKER, port=MQTT_PORT)

    # Inicializa MQTTReader y QueueConsumer
    mqtt_reader = MQTTReader(client=client, topic="esp32/buttons", output_queue=received_queue)
    queue_consumer = QueueConsumer(input_queue=received_queue, redis_latest=redis_latest, redis_history=redis_history)

    # Inicia los hilos
    mqtt_reader_thread = threading.Thread(target=mqtt_reader.runner, name="MQTTReader")
    mqtt_reader_thread.start()

    queue_consumer_thread = threading.Thread(target=queue_consumer.runner, name="QueueConsumer")
    queue_consumer_thread.start()

    # Ejecución hasta que se detenga la aplicación
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping security worker...")
        mqtt_reader.stop()
        queue_consumer.stop()

    # Espera a que terminen los hilos
    mqtt_reader_thread.join()
    queue_consumer_thread.join()
    logging.info("Security worker stopped.")

if __name__ == "__main__":
    main()
