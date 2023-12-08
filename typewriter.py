""""Module that operates the typewriter."""
#!/usr/bin/python
# -*- coding:utf-8 -*-

#!.venv/bin/python
import sys
import io
import textwrap
import os
import keyboard
import google.generativeai as palm
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from working_functions import display_image_8bpp_memory
from IT8951.display import AutoEPDDisplay

#palm.configure(api_key=os.environ['API_KEY'])
palm.configure(api_key="REDACTED_API_KEY")

print('Initializing EPD...')

# here, spi_hz controls the rate of data transfer to the device, so a higher
# value means faster display refreshes. the documentation for the IT8951 device
# says the max is 24 MHz (24000000), but my device seems to still work as high as
# 80 MHz (80000000)
display = AutoEPDDisplay(vcom=-1.70, rotate='CCW', spi_hz=24000000)

# Ensure this matches your particular screen
WIDTH = 1872
HEIGHT = 1404
SCREEN_SIZE = (HEIGHT, WIDTH)

# Define font and print characteristics
FONTSIZE = 48
LINE_LENGTH = 54
SPACING = 12
ALIGNMENT = "center"

# Define locations
X_OFFSET = 10
Y_OFFSET = 10
DRAW_POINT = (X_OFFSET, Y_OFFSET)

# Colors
BACK = 255
FORE = 0

# Font
# FONT_FILEPATH = '/usr/share/fonts/TTF/DejaVuSans.ttf'
FONT_FILEPATH = 'remington_noiseless.ttf'

TEXT = "Long enough text for the purpose of quickly testing how \
multiline splits work this should be enough. Now we need a bunch \
more text so that I can save time. 1 2 3 4 5 6 7 8 9 0. \
Long enough text for the purpose of quickly testing how multiline \
splits work this should be enough. Now we need a bunch more test so \
that I can save time. 1 2 3 4 5 6 7 8 9 0"

#TEXT = ""

font = ImageFont.truetype(FONT_FILEPATH, size=FONTSIZE)

#Debugging display
print('VCOM set to', display.epd.get_vcom())

while 1:

    # capture with record and add new loop for each space
    recorded = keyboard.record('space')

    RECORDEDSTR = ''.join(list(keyboard.get_typed_strings(recorded, allow_backspace=True)))
    #print(RECORDEDSTR)

    match RECORDEDSTR:
        case 'clear ' | 'c ' | 'clr ':
            TEXT = ""
        case 'bard ' | 'b ':
            response = palm.generate_text(prompt = TEXT)
            TEXT = response.result
        case other:
            TEXT = TEXT + RECORDEDSTR

    LINES = textwrap.fill(TEXT, LINE_LENGTH)
    #çprint(LINES)

    # Draw image
    #img = Image.new("L", font.getmask(LINES).size, BACKGROUND)
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
