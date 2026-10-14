FROM ubuntu:24.04

RUN apt update && apt install -y python3-pip python3-lgpio python3-libgpiod python3-evdev && rm -rf /var/lib/apt/lists/*
# Pinned so a rebuild never silently picks up an incompatible MQTT library (logic.py needs paho-mqtt 2.x)
RUN pip3 install --no-cache-dir --break-system-packages \
	gpiozero==2.0.1 \
	ha-mqtt-discoverable==0.26.0 \
	paho-mqtt==2.1.0 \
	tzdata

# RUN apt install -y python3-pip python3-lgpio python3-rgpio
# RUN pip3 install RPi.GPIO

#COPY "./database.sqlite3" "/database.sqlite3"
COPY "./config.py" "/config.py"
COPY "./db_utils.py" "/db_utils.py"
COPY "./logic.py" "/logic.py"

CMD ["python3", "-u", "logic.py"]
