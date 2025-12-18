'''
This file contains various functions to test different aspects
of the module's display capabilities. Each function takes only
an AutoDisplay object (or, probably, an object of a type derived
from that class) as an argument, so they can be used with either
an actual AutoEPDDisplay, or a VirtualEPDDisplay, or something else.

See test.py for an example.
'''

# functions defined in this file
__all__ = [
    'print_system_info',
    'clear_display',
    'display_image_8bpp',
    'display_image_8bpp_memory',
    'partial_update'
]
from sys import path
from PIL import Image, ImageDraw, ImageFont
path += ['../../']
from IT8951 import constants

def print_system_info(display):
    """Function printing python version."""
    epd = display.epd
    print('System info:')
    print(f'  display size: {epd.width}x{epd.height}')
    print(f'  img buffer address: {epd.img_buf_address:X}')
    print(f'  firmware version: {epd.firmware_version}')
    print(f'  LUT version: {epd.lut_version}')
    print()

def clear_display(display):
    """Function printing python version."""
    print('Clearing display...')
    display.clear()

def display_image_8bpp(display, img_path):
    """Function printing python version."""
    print(f'Displaying "{img_path}"...')

    # clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    img = Image.open(img_path)

    dims = (display.width, display.height)

    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    display.frame_buf.paste(img, paste_coords)

    display.draw_full(constants.DisplayModes.GC16)
    #display.draw_partial(constants.DisplayModes.DU)

def display_image_8bpp_memory (display, img_data):
    """Function printing python version."""
    #print('Displaying "{}"...'.format(img))

    #clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    img = Image.open(img_data)

    dims = (display.width, display.height)

    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    display.frame_buf.paste(img, paste_coords)

    #display.draw_full(constants.DisplayModes.GC16)
    display.draw_partial(constants.DisplayModes.DU)

def partial_update(display):
    """Function printing python version."""
    print('Starting partial update...')

    # clear image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    print('  writing full...')
    _place_text(display.frame_buf, 'partial', x_offset=-display.width//4)
    display.draw_full(constants.DisplayModes.GC16)

    # should use 1bpp for partial text update
    print('  writing partial...')
    _place_text(display.frame_buf, 'update', x_offset=+display.width//4)
    display.draw_partial(constants.DisplayModes.DU)

def _place_text(img, text, x_offset=0, y_offset=0):
    """This function is just a helper for the others."""

    fontsize = 80

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    img_width, img_height = img.size
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = fontsize

    draw_x = (img_width - text_width)//2 + x_offset
    draw_y = (img_height - text_height)//2 + y_offset

    draw.text((draw_x, draw_y), text, font=font)
