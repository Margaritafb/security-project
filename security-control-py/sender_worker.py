import requests
import time
import serial  

# Configuración de la API
API_BASE_URL = "http://api:8000"  

# Configuración de conexión serial
#SERIAL_PORT = "COM4"  # Cambia según el puerto serial disponible
#BAUD_RATE = 115200  # Ajustar el baudrate según el dispositivo
#ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)  # Inicializar el puerto serial

def get_sensor_data(sensor_id):
    """
    Consulta el endpoint de la API para obtener el bytearray del sensor.
    
    Args:
        sensor_id (int): ID del sensor a consultar.

    Returns:
        bytearray: Array de bytes recibido desde la API.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/send_latest/{sensor_id}")
        response.raise_for_status()  # Lanza una excepción si el estado no es 200
        return bytearray(response.content)
    except requests.RequestException as e:
        print(f"Error al obtener datos del sensor {sensor_id}: {e}")
        return None

def send_to_serial(data):
    """
    Envía el bytearray directamente a través del puerto serial.
    
    Args:
        data (bytearray): Datos a enviar.
    """
    # Enviar directamente el bytearray al puerto serial
    #ser.write(data)

    # Imprimir en consola para depuración
    print(f"Enviando bytearray al puerto serial: {list(data)}")

def main():
    sensor_ids = [1, 2, 3]  # IDs de los sensores a procesar
    while True:
        for sensor_id in sensor_ids:
            print(f"\n[INFO] Procesando sensor {sensor_id}...")
            sensor_data = get_sensor_data(sensor_id)
            if sensor_data:
                if len(sensor_data) == 9:  # Validar que el mensaje tenga exactamente 9 bytes
                    send_to_serial(sensor_data)
                else:
                    print(f"[ERROR] El mensaje del sensor {sensor_id} no tiene 9 bytes: {len(sensor_data)} bytes")
            else:
                print(f"[ERROR] No se pudo obtener datos para el sensor {sensor_id}.")
            
            # Esperar 15 segundos antes de procesar el siguiente sensor
            time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Sender Worker detenido.")

