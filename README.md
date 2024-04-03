# AccessControl
## Gate Access Control Overiew

Python code intended to be used for a gate access control system. Code will connect to sqlite db and create a search codes.
It will create, update and search codes against SQLite DB. Keyboard input it will query DB and based on code will trigger different GPIO pins. 

## Physical Setup
GPIO pins should be hooked up to external relay to interface with gate motor controller and automatic door lock.

## Virtual Setup


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


