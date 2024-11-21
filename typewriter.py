""""Module that operates the typewriter."""
#!/usr/bin/python
# -*- coding:utf-8 -*-

#!.venv/bin/python
import sys
import io
import math
import textwrap
#import os
import keyboard
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from working_functions import display_image_8bpp_memory
from IT8951.display import AutoEPDDisplay

#palm.configure(api_key=os.environ['API_KEY'])
#palm.configure(api_key="REDACTED_API_KEY")

#print('Initializing EPD...')

# here, spi_hz controls the rate of data transfer to the device, so a higher
# value means faster display refreshes. the documentation for the IT8951 device
# says the max is 24 MHz (24000000), but my device seems to still work as high as
# 80 MHz (80000000)
display = AutoEPDDisplay(vcom=-1.70, rotate='CCW', spi_hz=24000000)

# blank the screen
display.clear()

# Ensure this matches your particular screen
WIDTH = 1400
#WIDTH = 1800
HEIGHT = 1404
#HEIGHT = 1000

SCREEN_SIZE = (HEIGHT, WIDTH)

# Define font and print characteristics
FONTSIZE = 48
LINE_LENGTH = 45
SPACING = 12
ALIGNMENT = "center"

# Define locations
FIXED_X_OFFSET = 150
START_Y_OFFSET = 150
START_DRAW_POINT = (FIXED_X_OFFSET, START_Y_OFFSET)

# Colors
BACK = 255
FORE = 0

# Font
FONT_FILEPATH = 'remington_noiseless.ttf'

START_TEXT = "And they are dancing, the board floor slamming \
under the jackboots and the fiddlers grinning hideously over \
their canted pieces. Towering over them all is the judge and \
he is naked dancing, his small feet lively and quick and now \
in doubletime and bowing to the ladies, huge and pale and hairless,\
like an enormous infant. He never sleeps, he says. He says \
he’ll never die. He bows to the fiddlers and sashays backwards \
and throws back his head and laughs deep in his throat and \
he is a great favorite, the judge. He wafts his hat and the \
lunar dome of his skull passes palely under the lamps and he \
swings about and takes possession of one of the fiddles and \
he pirouettes and makes a pass, two passes, dancing and \
fiddling at once. His feet are light and nimble. He never \
sleeps. He says that he will never die. He dances in light \
and in shadow and he is a great favorite. He never sleeps, \
the judge. He is dancing, dancing. He says that he will never die. \
                                                                  "

DRAW_POINT = START_DRAW_POINT
Y_OFFSET = START_Y_OFFSET

font = ImageFont.truetype(FONT_FILEPATH, size=FONTSIZE)

#Debugging display
#print('VCOM set to', display.epd.get_vcom())

TEXT = START_TEXT

while 1:

    # capture with read_key and interpret special keys
    recorded = keyboard.read_key()
    match recorded:
        case 'space':
            TEXT = TEXT + " "
        case 'backspace':
            TEXT = TEXT[:-1]
        case 'enter':
            TEXT = TEXT + " \n "
        case other:
            TEXT = TEXT + recorded

    LINES = textwrap.fill(TEXT, LINE_LENGTH)
    #print(LINES)

    #Y_OFFSET = Y_OFFSET - (math.floor(len(TEXT)*0.00700)*70)
    Y_OFFSET = Y_OFFSET - (math.floor(len(TEXT)*0.00700))
    #print (len(TEXT))
    #print (Y_OFFSET)
    DRAW_POINT = (FIXED_X_OFFSET, Y_OFFSET)
    #print (DRAW_POINT)

    # Draw image
    img = Image.new("L", SCREEN_SIZE, BACK)
    draw = ImageDraw.Draw(img)
    draw.multiline_text(DRAW_POINT, LINES, font=font, fill=FORE, spacing=SPACING, align=ALIGNMENT)
    text_window = img.getbbox()
    img = img.crop(text_window)

    # Save file in memory only
    buf = io.BytesIO()
    img.save(buf, format='PNG')

    # Display image from memory
    display_image_8bpp_memory(display, buf)

sys.exit()
