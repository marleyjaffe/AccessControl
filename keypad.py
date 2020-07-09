#https://github.com/brettmclean/pad4pi
'''
TODO:	Append key press to string unless # (enter) value is chosen
		# keypress sends string to gate logic
		* keypress clears string
		A-D keypress goes to ring function
		Any keypress lights up keypad LED's
		Send completed keypress or results to HomeAssistant websocket
		Keypress timeout logic 
		pip install pad4pi

'''		

from pad4pi import rpi_gpio


KEYPAD = [
    [1, 2, 3, "A"],
    [4, 5, 6, "B"],
    [7, 8, 9, "C"],
    ["*", 0, "#", "D"]
]

ROW_PINS = [4, 14, 15, 17] # BCM numbering (keypad Pin #1, 2, 8, 7)
COL_PINS = [18, 27, 22] # BCM numbering (keypad Pin #3, 4, 5, 6)

factory = rpi_gpio.KeypadFactory()

# Try factory.create_4_by_3_keypad
# and factory.create_4_by_4_keypad for reasonable defaults
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS, gpio_mode=GPIO.BOARD)

def printKey(key):
    print(key)

# printKey will be called each time a keypad button is pressed
keypad.registerKeyPressHandler(printKey)