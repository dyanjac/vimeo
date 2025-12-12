FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY main.py .

# Copiar scripts desde la carpeta docker/
COPY docker/run_all.sh docker/set_env_secrets.sh ./

# Arreglar saltos de línea de Windows y dar permisos de ejecución
RUN sed -i 's/\r$//' run_all.sh set_env_secrets.sh && \
    chmod +x run_all.sh set_env_secrets.sh

EXPOSE 8014

ENTRYPOINT ["./run_all.sh"]
