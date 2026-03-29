FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data directory for persistent config and beacons
RUN mkdir -p /data
ENV CONFIG_FILE=/data/config.json
ENV BEACONS_FILE=/data/beacons.json

EXPOSE 5000

CMD ["python", "app.py"]
