FROM ubuntu:23.04

RUN apt update
RUN apt install -y python3-pip python3-lgpio python3-libgpiod
RUN pip3 install gpiozero --break-system-packages
RUN pip3 install ha_mqtt_discoverable --break-system-packages
RUN pip3 install evdev --break-system-packages

# RUN apt install -y python3-pip python3-lgpio python3-rgpio
# RUN pip3 install RPi.GPIO

#COPY "./database.sqlite3" "/database.sqlite3"
COPY "./db_utils.py" "/db_utils.py"
COPY "./logic.py" "/logic.py"

CMD ["python3", "-u", "logic.py"]
