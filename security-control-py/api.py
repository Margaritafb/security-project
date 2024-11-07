import json
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from redis import Redis
import uvicorn

app = FastAPI()

# Configuración de conexión a Redis

redis_latest = Redis(host="redis-latest", port=6379, db=0)
redis_history = Redis(host="redis-history", port=6380, db=0)

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
