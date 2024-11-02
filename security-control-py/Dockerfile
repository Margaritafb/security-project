# Dockerfile

# Usa una imagen base oficial de Python 3.11 slim
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos y lo instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de security-worker a /app
COPY . .

# Comando para ejecutar el worker
CMD ["python", "security-worker.py"]
