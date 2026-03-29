FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Version passed in from GitHub Actions at build time
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Data directory for persistent config and beacons
RUN mkdir -p /data
ENV CONFIG_FILE=/data/config.json
ENV BEACONS_FILE=/data/beacons.json

EXPOSE 5000

CMD ["python", "app.py"]
