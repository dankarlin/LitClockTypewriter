""""Module that operates the typewriter."""
#!/usr/bin/python
# -*- coding:utf-8 -*-

#!.venv/bin/python
import sys
import io
import math
import textwrap
import os
import threading
import queue
import time
import re
from datetime import datetime
import evdev
from evdev import ecodes
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from working_functions import display_image_8bpp_memory
from IT8951.display import AutoEPDDisplay
from literature_clock import LiteratureClockData, download_csv_data

# Configure Google API key from environment variable
# Set API_KEY in your .env file or environment
#palm.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

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

# Key mapping for evdev to handle special keys
KEY_MAP = {
    ecodes.KEY_SPACE: 'space',
    ecodes.KEY_BACKSPACE: 'backspace',
    ecodes.KEY_ENTER: 'enter',
    ecodes.KEY_SEMICOLON: ';',
    ecodes.KEY_LEFTSHIFT: None,  # Modifier, handled separately
    ecodes.KEY_RIGHTSHIFT: None,  # Modifier, handled separately
}

def clean_quote_text(quote_text):
    """Remove HTML tags and clean up quote text.

    Args:
        quote_text: Raw quote text from CSV

    Returns:
        Cleaned quote text
    """
    if not quote_text:
        return quote_text

    # Remove HTML tags (like <br>, <br/>, </br>, etc.)
    text = re.sub(r'<[^>]+>', ' ', quote_text)

    # Remove standalone digital timestamps like "00:00:00" or "12:37:45"
    # These appear alone after HTML breaks
    text = re.sub(r'\s+\d{1,2}:\d{2}:\d{2}\s+', ' ', text)

    # Remove standalone AM/PM timestamps like "12:37 AM" that appear isolated
    # But preserve them if they're part of a sentence (followed by punctuation or lowercase)
    # This matches timestamps that are followed by whitespace or end of string
    text = re.sub(r'\s+\d{1,2}:\d{2}\s*[AP]M(?=\s|$)', ' ', text)

    # Also remove at the start
    text = re.sub(r'^\s*\d{1,2}:\d{2}\s*[AP]M\s*', '', text)

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Clean up leading/trailing whitespace
    text = text.strip()

    return text

def find_typewriter_device():
    """Find the USB Typewriter keyboard device.

    Returns:
        evdev.InputDevice: The typewriter device

    Raises:
        RuntimeError: If device not found
    """
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    # First, look specifically for typewriter
    for device in devices:
        if 'typewriter' in device.name.lower():
            print(f"Found USB Typewriter: {device.name} at {device.path}")
            return device

    # Second, look for USB keyboard (not virtual or HDMI)
    for device in devices:
        name_lower = device.name.lower()
        if 'keyboard' in name_lower and 'virtual' not in name_lower and 'hdmi' not in name_lower:
            print(f"Found keyboard device: {device.name} at {device.path}")
            return device

    # Finally, try to find any device with keyboard capabilities
    for device in devices:
        capabilities = device.capabilities()
        # Check if device has keyboard keys
        if ecodes.EV_KEY in capabilities:
            keys = capabilities[ecodes.EV_KEY]
            # Check for common letter keys
            if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                name_lower = device.name.lower()
                # Skip virtual and HDMI devices
                if 'virtual' not in name_lower and 'hdmi' not in name_lower:
                    print(f"Using keyboard device: {device.name} at {device.path}")
                    return device

    raise RuntimeError("No keyboard device found!")

class TypewriterApp:
    """Main application class for the typewriter with clock mode support."""

    def __init__(self, display_obj, font_obj, kbd_device):
        """Initialize the typewriter application.

        Args:
            display_obj: AutoEPDDisplay instance
            font_obj: PIL ImageFont instance
            kbd_device: evdev.InputDevice for the keyboard
        """
        self.display = display_obj
        self.font = font_obj
        self.keyboard_device = kbd_device
        self.mode = "clock"  # Start in clock mode by default
        self.command_buffer = ""  # Track last 6 chars for ;clock detection
        self.text = ""  # Start with empty text for clock mode
        self.y_offset = START_Y_OFFSET
        self.clock_data = None
        self.clock_quotes = []  # Store recent quotes for clock mode
        self.event_queue = queue.Queue()
        self.running = True
        self.shift_pressed = False

    def keyboard_read_loop(self):
        """Background thread that reads keyboard events from evdev."""
        last_event_time = 0
        min_event_interval = 0.05  # Minimum 50ms between key events (debounce)

        try:
            for event in self.keyboard_device.read_loop():
                if not self.running:
                    break

                if event.type == ecodes.EV_KEY:
                    key_event = evdev.categorize(event)

                    # Track shift state
                    if key_event.keycode in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                        self.shift_pressed = key_event.keystate == key_event.key_down
                        continue

                    # Only process key down events
                    if key_event.keystate == key_event.key_down:
                        # Simple debouncing - ignore events that come too quickly
                        current_time = time.time()
                        if current_time - last_event_time < min_event_interval:
                            continue

                        char = self._evdev_key_to_char(key_event.keycode)
                        if char:
                            self.event_queue.put(('key', char))
                            last_event_time = current_time

        except OSError:
            # Device disconnected
            print("Keyboard device disconnected")
            self.running = False

    def _evdev_key_to_char(self, keycode):
        """Convert evdev keycode to character.

        Args:
            keycode: evdev key code (string like 'KEY_A')

        Returns:
            Character string or None
        """
        # Handle special keys first
        if keycode == 'KEY_SPACE':
            return 'space'
        elif keycode == 'KEY_BACKSPACE':
            return 'backspace'
        elif keycode == 'KEY_ENTER':
            return 'enter'

        # Handle letter keys (KEY_A through KEY_Z)
        if keycode.startswith('KEY_') and len(keycode) == 5:
            char = keycode[4].lower()  # Extract letter and lowercase it
            if 'a' <= char <= 'z':
                return char.upper() if self.shift_pressed else char

        # Handle number keys (KEY_0 through KEY_9)
        if keycode.startswith('KEY_') and len(keycode) == 5:
            char = keycode[4]
            if '0' <= char <= '9':
                # Handle shift for number keys
                shift_map = {
                    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'
                }
                return shift_map[char] if self.shift_pressed else char

        # Handle punctuation
        punct_map = {
            'KEY_SEMICOLON': ';' if not self.shift_pressed else ':',
            'KEY_COMMA': ',',
            'KEY_DOT': '.',
            'KEY_SLASH': '/',
            'KEY_APOSTROPHE': "'",
            'KEY_MINUS': '-',
            'KEY_EQUAL': '=',
            'KEY_LEFTBRACE': '[',
            'KEY_RIGHTBRACE': ']',
            'KEY_BACKSLASH': '\\',
        }

        if keycode in punct_map:
            return punct_map[keycode]

        return None

    def clock_update_loop(self):
        """Background thread that checks for minute changes and updates clock display."""
        last_minute = None

        while self.running:
            if self.mode == "clock":
                current = datetime.now()
                current_minute = (current.hour, current.minute)

                # Update on minute boundary
                if current_minute != last_minute:
                    self.event_queue.put(('clock_update', current))
                    last_minute = current_minute

            time.sleep(5)  # Check every 5 seconds (plenty fast enough for minute changes)

    def _handle_keystroke(self, key):
        """Handle a keystroke event.

        Args:
            key: Key name from keyboard event
        """
        # Exit clock mode on any key press
        if self.mode == "clock":
            self.mode = "typewriter"
            # Start fresh in typewriter mode
            self.text = ""
            self.y_offset = START_Y_OFFSET
            print("Switched to typewriter mode. Type ';clock' to return to clock mode.")
            # Don't render immediately - wait for display to be ready
            # The next keystroke will trigger rendering
            return

        # Accumulate command buffer (keep last 6 chars)
        self.command_buffer += key
        if len(self.command_buffer) > 6:
            self.command_buffer = self.command_buffer[-6:]

        # Check for ;clock command
        if self.command_buffer.endswith(';clock'):
            self._enter_clock_mode()
            self.command_buffer = ""
            return

        # Normal typewriter processing
        self._process_typewriter_key(key)

    def _process_typewriter_key(self, key):
        """Process a keystroke in typewriter mode.

        Args:
            key: Key name from keyboard event
        """
        # Handle special keys
        match key:
            case 'space':
                self.text = self.text + " "
            case 'backspace':
                self.text = self.text[:-1]
            case 'enter':
                self.text = self.text + " \n "
            case _:
                self.text = self.text + key

        # Render with error handling
        try:
            self._render_typewriter()
        except TimeoutError:
            print("Display busy, keystroke buffered")
            # Text is already updated, will render on next keystroke

    def _render_typewriter(self):
        """Render and display the current typewriter text."""
        lines = textwrap.fill(self.text, LINE_LENGTH)

        # Dynamic Y-offset calculation (same as original)
        self.y_offset = self.y_offset - (math.floor(len(self.text)*0.00700))
        draw_point = (FIXED_X_OFFSET, self.y_offset)

        # Draw image (same as original)
        img = Image.new("L", SCREEN_SIZE, BACK)
        draw = ImageDraw.Draw(img)
        draw.multiline_text(draw_point, lines, font=self.font, fill=FORE,
                          spacing=SPACING, align=ALIGNMENT)
        text_window = img.getbbox()
        img = img.crop(text_window)

        # Save file in memory only
        buf = io.BytesIO()
        img.save(buf, format='PNG')

        # Wait for display to be ready before updating
        try:
            self.display.epd.wait_display_ready()
        except Exception:  # pylint: disable=broad-except
            pass  # If wait fails, continue anyway

        # Display image from memory
        display_image_8bpp_memory(self.display, buf)

    def _enter_clock_mode(self):
        """Enter clock mode and display the current time's quote."""
        self.mode = "clock"

        # Clock data is already loaded at startup
        # Reset clock quotes to start fresh
        self.clock_quotes = []

        print("Entered clock mode. Press any key to return to typewriter mode.")

        # Display current time's quote immediately
        self._update_clock_display(datetime.now())

    def _update_clock_display(self, current_time):
        """Update the clock display with a quote for the current time.

        Args:
            current_time: datetime object
        """
        hour = current_time.hour
        minute = current_time.minute

        # Get quote from data
        quote_data = self.clock_data.get_quote(hour, minute)

        if quote_data is None:
            display_text = f"No quote found for {hour:02d}:{minute:02d}"
        else:
            # Clean the quote text (remove HTML tags and timestamps)
            display_text = clean_quote_text(quote_data['quote'])

        # Add to quotes list (keep last 15 quotes max)
        # With top overflow allowed, we can show more quotes
        self.clock_quotes.append(display_text)
        if len(self.clock_quotes) > 15:
            self.clock_quotes.pop(0)  # Remove oldest

        # Render clock display
        try:
            self._render_clock_display()
        except TimeoutError:
            print(f"Display busy, skipping update for {hour:02d}:{minute:02d}")

    def _render_clock_display(self):
        """Render clock mode display with recent quotes."""
        # Combine all quotes with spacing
        all_quotes = []
        for quote in self.clock_quotes:
            wrapped = textwrap.fill(quote, LINE_LENGTH)
            all_quotes.append(wrapped)

        # Join with blank lines for spacing
        combined_text = "\n\n\n".join(all_quotes)

        # Create full-size image using ACTUAL display dimensions (not constants)
        # The display after rotation is larger than the constants suggest
        actual_size = (self.display.width, self.display.height)
        img = Image.new("L", actual_size, BACK)
        draw = ImageDraw.Draw(img)

        # Get actual image dimensions
        _, img_height = img.size

        # Calculate text height to position from bottom
        bbox = draw.multiline_textbbox((0, 0), combined_text, font=self.font, spacing=SPACING)
        text_height = bbox[3] - bbox[1]

        # Position so the text ends near the bottom of the screen
        # Use actual image height (1400), not HEIGHT constant (1404)
        bottom_margin = 50  # Very small margin to push text higher
        y_position = img_height - text_height - bottom_margin

        # Allow text to overflow at the top - older quotes get cut off naturally
        # y_position can be negative if text is taller than screen
        print(f"Clock display: {len(self.clock_quotes)} quotes, "
              f"text_height={text_height}px, y_position={y_position}px")

        draw_point = (FIXED_X_OFFSET, y_position)

        # Draw the text on the full-size image
        draw.multiline_text(draw_point, combined_text, font=self.font, fill=FORE,
                          spacing=SPACING, align=ALIGNMENT)

        # DON'T crop - keep full screen size so display_image_8bpp_memory
        # doesn't reposition it to the bottom

        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format='PNG')

        # Wait for display to be ready
        try:
            self.display.epd.wait_display_ready()
        except Exception:  # pylint: disable=broad-except
            pass

        # Display
        display_image_8bpp_memory(self.display, buf)

    def run(self):
        """Main event loop."""
        # Load clock data at startup
        csv_path = '/home/dan/Typewriter/literature/litclock_annotated.csv'
        if not os.path.exists(csv_path):
            try:
                download_csv_data(csv_path)
            except Exception as err:
                print(f"Error downloading CSV data: {err}")

        try:
            self.clock_data = LiteratureClockData(csv_path)
        except Exception as err:
            print(f"Error loading clock data: {err}")

        # Display initial quote
        print("Starting in clock mode. Press any key to switch to typewriter mode.")
        self._update_clock_display(datetime.now())

        # Start keyboard reading thread
        keyboard_thread = threading.Thread(target=self.keyboard_read_loop, daemon=True)
        keyboard_thread.start()

        # Start clock update thread
        clock_thread = threading.Thread(target=self.clock_update_loop, daemon=True)
        clock_thread.start()

        # Main event processing loop
        try:
            while self.running:
                try:
                    event_type, data = self.event_queue.get(timeout=0.1)

                    if event_type == 'key':
                        self._handle_keystroke(data)
                    elif event_type == 'clock_update':
                        self._update_clock_display(data)

                except queue.Empty:
                    continue

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False


# Initialize and run the application
if __name__ == "__main__":
    try:
        # Find the USB typewriter keyboard device
        keyboard_device = find_typewriter_device()

        # Create and run the app
        app = TypewriterApp(display, font, keyboard_device)
        app.run()

    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    sys.exit()
