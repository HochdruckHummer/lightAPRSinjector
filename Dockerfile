FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Version passed in from GitHub Actions at build time
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
ENV PYTHONUNBUFFERED=1

# Data directory for persistent config and beacons
RUN useradd --system --no-create-home app && mkdir -p /data && chown app:app /data
ENV CONFIG_FILE=/data/config.json
ENV BEACONS_FILE=/data/beacons.json

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "app.py"]
