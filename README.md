# AccessControl
## Gate Access Control Overiew

Python code intended to be used for a gate access control system. Code will connect to sqlite db and create a search codes.
It will create, update and search codes against SQLite DB. Keyboard input it will query DB and based on code will trigger different GPIO pins. 

## Physical Setup
GPIO pins should be hooked up to external relay to interface with gate motor controller and automatic door lock.

## Docker Setup
First, make soft-links to the keyboards since you can't pass paths that have variables:
ln -s /dev/input/by-path/platform-xhci-hcd.1-usb-0:2:1.0-event-kbd /dev/input/by-path/keypad1
Add user to docker groups:
### Create docker group (should already exist)
sudo groupadd docker

### Add user to docker group
sudo usermod -aG docker $USER

### Log in to new group (alternatively restart the Pi)
newgrp docker

### Use this to build and run (run in forground)
docker build -t accesscontrol . && docker run --device /dev/gpiochip4:/dev/gpiochip4 --device /dev/input/by-path/keypad1:/dev/input/by-path/keypad1 --device /dev/input/by-path/keypad2:/dev/input/by-path/keypad2 accesscontrol

### Use to run prebuilt in background
docker run -d --device /dev/gpiochip4:/dev/gpiochip4 --device /dev/input/by-path/keypad1:/dev/input/by-path/keypad1 --device /dev/input/by-path/keypad2:/dev/input/by-path/keypad2 --restart always --name AccessControl accesscontrol

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


