# AccessControl
## Gate Access Control Overiew

Python code intended to be used for a gate access control system. Code will connect to sqlite db and create a search codes.
It will create, update and search codes against SQLite DB. Keyboard input it will query DB and based on code will trigger different GPIO pins. 

## Physical Setup
GPIO pins should be hooked up to external relay to interface with gate motor controller and automatic door lock.

### Reed switches
Wired between GPIO and GND using the Pi's internal pull-up (magnet present / closed = LOW). Each is published to Home Assistant as an MQTT binary sensor (device class `opening`, on = open).

| Sensor    | BCM GPIO | Physical pin |
|-----------|----------|--------------|
| Gate      | 23       | 16           |
| Mailbox 1 | 24       | 18           |
| Mailbox 2 | 25       | 22           |
| GND       | -        | 20           |

## Docker Setup
First, make soft-links to the keyboards since you can't pass paths that have variables:
Add the following to `sudo crontab -e` to keep persistent through reboots:
@reboot ln -s /dev/input/by-path/platform-xhci-hcd.1-usb-0:2:1.0-event-kbd /dev/input/by-path/keypad1
@reboot ln -s /dev/input/by-path/platform-xhci-hcd.0-usb-0:2:1.0-event-kbd /dev/input/by-path/keypad2

### Create docker group (should already exist)
sudo groupadd docker

### Add user to docker group
sudo usermod -aG docker $USER

### Log in to new group (alternatively restart the Pi)
newgrp docker

### Use this to build and run (run in forground)
docker build -t accesscontrol . && docker run -e MQTT_HOST=10.10.10.3 -e MQTT_BASE_NAME=Catt --device /dev/gpiochip4:/dev/gpiochip4 --device /dev/input/by-path/keypad1:/dev/input/by-path/keypad1 --device /dev/input/by-path/keypad2:/dev/input/by-path/keypad2 -v ~/AccessControl/database.sqlite3:/database.sqlite3 accesscontrol

### Use to run prebuilt in background
docker run -d -e MQTT_HOST=10.10.10.3 -e MQTT_BASE_NAME=Catt --device /dev/gpiochip4:/dev/gpiochip4 --device /dev/input/by-path/keypad1:/dev/input/by-path/keypad1 --device /dev/input/by-path/keypad2:/dev/input/by-path/keypad2 -v ~/AccessControl/database.sqlite3:/database.sqlite3 --restart always --name AccessControl accesscontrol

## Configuration
All site-specific values come from environment variables. `MQTT_HOST` and `MQTT_BASE_NAME` are required; the container exits at startup if either is missing. Everything else has a default. Invalid numbers also stop the container at startup.

### Docker compose example
```yaml
services:
  accesscontrol:
    image: accesscontrol:1
    container_name: AccessControl
    restart: always
    environment:
      TZ: America/Los_Angeles
      MQTT_HOST: 10.10.10.3
      MQTT_BASE_NAME: Catt
      # MQTT_USERNAME: accesscontrol
      # MQTT_PASSWORD_FILE: /run/secrets/mqtt_password
    # env_file: .env   # alternative to listing variables inline
    volumes:
      - ~/docker/AccessControl/database.sqlite3:/database.sqlite3
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    devices:
      - /dev/gpiochip4:/dev/gpiochip4
      - /dev/input/by-path/keypad1:/dev/input/by-path/keypad1
      - /dev/input/by-path/keypad2:/dev/input/by-path/keypad2
```
If you change `KEYPAD_*_DEVICE` or `DB_PATH`, update the matching `devices:` / `volumes:` container paths. The same applies to the gpiochip.

### General
| Variable    | Default               | Description |
|-------------|-----------------------|-------------|
| `TZ`        | `America/Los_Angeles` | Timezone used for timestamps sent to HA |
| `LOG_LEVEL` | `INFO`                | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DB_PATH`   | `/database.sqlite3`   | SQLite database path inside the container (directory of `db_utils.py`) |

### MQTT / Home Assistant
| Variable                | Default            | Description |
|-------------------------|--------------------|-------------|
| `MQTT_HOST`             | required           | Broker IP or hostname |
| `MQTT_PORT`             | `1883`             | Broker port |
| `MQTT_USERNAME`         | none               | Broker username |
| `MQTT_PASSWORD`         | none               | Broker password |
| `MQTT_PASSWORD_FILE`    | none               | Path to a file containing the password (docker secrets). Takes precedence over `MQTT_PASSWORD` |
| `MQTT_DISCOVERY_PREFIX` | `homeassistant`    | HA MQTT discovery prefix |
| `MQTT_BASE_NAME`        | required           | HA device name becomes `<name>-AccessControl` |
| `MQTT_BASE_IDENTIFIER`  | `MQTT_BASE_NAME` lowercased | Prefix for entity IDs, e.g. `<id>-gatepi-gate-open`. Changing it creates new entities in HA |

### GPIO (BCM numbering)
| Variable            | Default | Description |
|---------------------|---------|-------------|
| `GATE_OPEN_PIN`     | `6`     | Gate open relay |
| `GATE_CLOSE_PIN`    | `13`    | Gate close relay |
| `GATE_STOP_PIN`     | `19`    | Gate stop relay |
| `LOCK_PIN`          | `26`    | Package lock relay |
| `GATE_REED_PIN`     | `23`    | Gate reed switch |
| `MAILBOX1_REED_PIN` | `24`    | Mailbox 1 reed switch |
| `MAILBOX2_REED_PIN` | `25`    | Mailbox 2 reed switch |
| `REED_BOUNCE_TIME`  | `0.1`   | Reed switch debounce (seconds) |

### Keypads
| Variable                 | Default                      | Description |
|--------------------------|------------------------------|-------------|
| `KEYPAD_OUTSIDE_DEVICE`  | `/dev/input/by-path/keypad1` | Outside keypad input device |
| `KEYPAD_INSIDE_DEVICE`   | `/dev/input/by-path/keypad2` | Inside keypad input device |
| `KEYPAD_CODE_MAX_LENGTH` | `9`                          | Max digits before the entry resets |
| `KEYPAD_CODE_TIMEOUT`    | `10`                         | Seconds between key presses before the entry resets |

### Timing (seconds)
| Variable                 | Default | Description |
|--------------------------|---------|-------------|
| `GATE_TOGGLE_LENGTH`     | `0.3`   | Relay pulse length for open/close |
| `GATE_PERSON_TIME`       | `10`    | Stop duration for person open |
| `GATE_STOP_HOLD_TIMEOUT` | `86400` | STOP is released and the gate closes after this |
| `GATE_HOLD_OPEN_TIMEOUT` | `3600`  | HOLD OPEN is released and the gate closes after this |
| `LOCK_UNLOCK_TIME`       | `15`    | Package lock unlock duration |

## Install Steps
curl https://pyenv.run | bash
follow steps for adding pyenv into .bashrc and .profile

pyenv install 3.10.13
export PATH=$PATH:/home/liq/.pyenv/versions/3.10.13/bin

sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

pyenv install 3.10.13
pyenv local 
sudo apt-get install pip

pip install ha-mqtt-discoverable
# maybe not - pip3 install RPi.GPIO
pip3 install evdev
pip3 install rpi-lgpio


