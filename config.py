'''
Runtime configuration from environment variables (set in docker compose `environment:` or an env_file).
See README "Configuration" for the full list.

Fatal errors exit via sys.exit(message) rather than logging so that importing this module
does not configure the root logger before logic.py does. Non-fatal problems are collected
in WARNINGS and logged by logic.py once logging is configured.

MQTT is optional: missing or invalid MQTT settings disable MQTT (MQTT_ENABLED = False)
instead of stopping the container, so the keypads and gate keep working offline.
'''

import os
import sys

WARNINGS = []

def env_str(name, default=None):
	value = os.environ.get(name, "").strip()
	return value if value else default

def env_int(name, default):
	value = env_str(name)
	try:
		return int(value) if value is not None else default
	except ValueError:
		sys.exit(f"CRITICAL- Environment variable {name} must be an integer, got {value!r}")

def env_float(name, default):
	value = env_str(name)
	try:
		return float(value) if value is not None else default
	except ValueError:
		sys.exit(f"CRITICAL- Environment variable {name} must be a number, got {value!r}")

# General
TZ = env_str("TZ", "America/Los_Angeles")
LOG_LEVEL = env_str("LOG_LEVEL", "INFO").upper()

# MQTT / Home Assistant (optional)
MQTT_HOST = env_str("MQTT_HOST")
MQTT_PORT = 1883
MQTT_USERNAME = env_str("MQTT_USERNAME")
MQTT_PASSWORD = env_str("MQTT_PASSWORD")
MQTT_DISCOVERY_PREFIX = env_str("MQTT_DISCOVERY_PREFIX", "homeassistant")
MQTT_BASE_NAME = env_str("MQTT_BASE_NAME")
MQTT_BASE_IDENTIFIER = env_str("MQTT_BASE_IDENTIFIER", MQTT_BASE_NAME.lower() if MQTT_BASE_NAME else None)
MQTT_ENABLED = MQTT_HOST is not None

def _disable_mqtt(reason):
	global MQTT_ENABLED
	MQTT_ENABLED = False
	WARNINGS.append(f"MQTT disabled: {reason}. Keypads and gate will run offline.")

if not MQTT_ENABLED:
	WARNINGS.append("MQTT disabled: MQTT_HOST is not set. Keypads and gate will run offline.")
else:
	if MQTT_BASE_NAME is None:
		_disable_mqtt("MQTT_BASE_NAME is not set")

	_port = env_str("MQTT_PORT")
	if _port is not None:
		try:
			MQTT_PORT = int(_port)
		except ValueError:
			_disable_mqtt(f"MQTT_PORT must be an integer, got {_port!r}")

	# MQTT_PASSWORD_FILE (docker secrets) takes precedence over MQTT_PASSWORD
	_password_file = env_str("MQTT_PASSWORD_FILE")
	if _password_file is not None:
		try:
			with open(_password_file) as f:
				MQTT_PASSWORD = f.read().strip()
		except OSError as error:
			_disable_mqtt(f"cannot read MQTT_PASSWORD_FILE {_password_file!r} ({error})")

# Relay outputs (BCM)
GATE_OPEN_PIN = env_int("GATE_OPEN_PIN", 6)
GATE_CLOSE_PIN = env_int("GATE_CLOSE_PIN", 13)
GATE_STOP_PIN = env_int("GATE_STOP_PIN", 19)
LOCK_PIN = env_int("LOCK_PIN", 26)

# Reed switch inputs (BCM)
GATE_REED_PIN = env_int("GATE_REED_PIN", 23)
MAILBOX1_REED_PIN = env_int("MAILBOX1_REED_PIN", 24)
MAILBOX2_REED_PIN = env_int("MAILBOX2_REED_PIN", 25)
REED_BOUNCE_TIME = env_float("REED_BOUNCE_TIME", 0.1)

# Keypads
KEYPAD_OUTSIDE_DEVICE = env_str("KEYPAD_OUTSIDE_DEVICE", "/dev/input/by-path/keypad1")
KEYPAD_INSIDE_DEVICE = env_str("KEYPAD_INSIDE_DEVICE", "/dev/input/by-path/keypad2")
KEYPAD_CODE_MAX_LENGTH = env_int("KEYPAD_CODE_MAX_LENGTH", 9)
KEYPAD_CODE_TIMEOUT = env_float("KEYPAD_CODE_TIMEOUT", 10)

# Gate / lock timing (seconds)
GATE_TOGGLE_LENGTH = env_float("GATE_TOGGLE_LENGTH", 0.3)
GATE_PERSON_TIME = env_float("GATE_PERSON_TIME", 10)
GATE_STOP_HOLD_TIMEOUT = env_float("GATE_STOP_HOLD_TIMEOUT", 60 * 60 * 24)
GATE_HOLD_OPEN_TIMEOUT = env_float("GATE_HOLD_OPEN_TIMEOUT", 60 * 60 * 1)
LOCK_UNLOCK_TIME = env_float("LOCK_UNLOCK_TIME", 15)
