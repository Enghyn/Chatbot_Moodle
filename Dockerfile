# Bot Moodle -> WhatsApp (Easypanel App / cualquier Docker host).
# El CMD corre el scheduler APScheduler en foreground (8:00/20:00);
# Easypanel espera un proceso vivo, por eso NO se usa cron del sistema.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/Argentina/Buenos_Aires

# tzdata para que APScheduler dispare 8:00/20:00 en hora local (ajustar TZ si cambia la zona)
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get purge -y --auto-remove && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Código primero: setuptools lo necesita presente para buildear el wheel
# (se pierde algo de cache de capas a cambio de un build que funciona)
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Se corre como root a proposito: Easypanel monta los volumenes como root y
# el proceso debe poder escribir estado.json en /data (bot personal, single-tenant).
RUN mkdir -p /data

ENV ESTADO_PATH=/data/estado.json

CMD ["python", "-m", "bot_moodle.main"]
