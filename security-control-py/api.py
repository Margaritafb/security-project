import json
from fastapi import FastAPI, HTTPException, Query, Response
from typing import Optional
from redis import Redis
import uvicorn
import serial
#hay que insalar pip install pyserial
from datetime import datetime

app = FastAPI()

# Configuración de conexión a Redis

redis_latest = Redis(host="redis-latest", port=6379, db=0)
redis_history = Redis(host="redis-history", port=6380, db=0)

# Configuración de conexión serial con el ESP32
#ESP32_PORT = "COM4"  # Cambia esto si el puerto es diferente
#ESP32_BAUDRATE = 115200  # Asegúrate de que el baudrate coincida con el ESP32
#ser = serial.Serial(ESP32_PORT, ESP32_BAUDRATE, timeout=1)

@app.get("/")
def read_root():
    """Ruta raíz de prueba."""
    return {"message": "API de Ssecurity-Control"}

@app.get("/latest/{sensor_id}")
def get_latest_reading(sensor_id: int):
    """
    Obtiene la última lectura de un sensor específico desde redis_latest.
    Args:
        sensor_id (int): Identificador del sensor.
    Returns:
        dict: Última lectura del sensor o mensaje de error si no existe.
    """
    data = redis_latest.hgetall(f"sensor:{sensor_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Sensor no encontrado en redis_latest")

    decoded_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
    return {"sensor_id": sensor_id, "latest_reading": decoded_data}

@app.get("/history/{sensor_id}")
def get_sensor_history(sensor_id: int, limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Obtiene el historial completo de lecturas de un sensor desde redis_history.
    Args:
        sensor_id (int): Identificador del sensor.
        limit (int, opcional): Número máximo de lecturas a devolver, por defecto 10.
    Returns:
        dict: Historial de lecturas del sensor.
    """
    readings = redis_history.lrange(f"sensor:{sensor_id}:history", -limit, -1)
    if not readings:
        raise HTTPException(status_code=404, detail="Historial no encontrado en redis_history")

    decoded_readings = [json.loads(reading.decode('utf-8')) for reading in readings]
    return {"sensor_id": sensor_id, "history": decoded_readings}

@app.get("/send_latest/{sensor_id}")
def send_latest_reading_to_esp32(sensor_id: int):
    """
    Construye un mensaje de 9 bytes con la última lectura del sensor usando el timestamp de Redis y lo retorna como un bytearray.
    """
    # Obtener datos del sensor desde Redis
    data = redis_latest.hgetall(f"sensor:{sensor_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Sensor no encontrado en redis_latest")

    # Decodificar datos desde Redis
    decoded_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
    sensor_state = int(decoded_data.get("sensor_state", 0))  # Estado del sensor, 0 por defecto
    timestamp = int(decoded_data.get("timestamp", 0))  # Timestamp almacenado en Redis

    # Decodificar el timestamp en día, mes, año, hora, minuto y segundo
    dt = datetime.fromtimestamp(timestamp)
    day, month, year, hour, minute, second = dt.day, dt.month, dt.year % 100, dt.hour, dt.minute, dt.second

    # Construir el mensaje de 9 bytes
    message = bytearray(9)
    message[0] = sensor_id  # ID del sensor
    message[1] = day        # Día
    message[2] = month      # Mes
    message[3] = year       # Año (últimos dos dígitos)
    message[4] = hour       # Hora
    message[5] = minute     # Minuto
    message[6] = second     # Segundo
    message[7] = sensor_state  # Estado del sensor

    # Calcular el checksum
    checksum = sum(message[:8]) & 0xFF
    message[8] = checksum

    # Retornar el mensaje como datos binarios
    return Response(content=bytes(message), media_type="application/octet-stream")
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
