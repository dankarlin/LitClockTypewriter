# eTypewriter

A modern e-ink display interface for vintage USB typewriters, running on Raspberry Pi. Features a classic typewriter mode and a literary clock mode that displays time-appropriate quotes from literature.

![finished product](IMG_2470.jpeg)

## Overview

This project transforms a USB typewriter into a beautiful e-ink writing experience. Type on a physical typewriter keyboard and see your words rendered in authentic typewriter font on a high-resolution e-ink display. The project includes a unique "literature clock" mode that displays literary quotes corresponding to the current time.

## Features

- **Typewriter Mode**: Real-time text rendering on e-ink display as you type
- **Literature Clock Mode**: Display time-based literary quotes from thousands of books
- **Vintage Aesthetics**: Authentic Remington Noiseless typewriter font
- **E-ink Display**: Easy-on-the-eyes, paper-like reading experience
- **Hardware Integration**: Works with USB typewriter keyboards via evdev
- **Mode Switching**: Toggle between modes with the `;clock` command

## Hardware Requirements

- Raspberry Pi (tested on models with SPI support)
- IT8951-based e-ink display (1400x1404 recommended)
- USB typewriter keyboard (or compatible USB keyboard)
- Power supply for Raspberry Pi

## Software Requirements

- Python 3.8+
- Raspberry Pi OS (or compatible Linux distribution)
- SPI enabled on Raspberry Pi

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dankarlin/LitClockTypewriter.git
cd LitClockTypewriter
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Install the IT8951 display driver:
```bash
pip install -e .
```

4. Enable SPI on your Raspberry Pi:
```bash
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
```

5. Download the literature clock data (happens automatically on first run):
```bash
python3 literature_clock.py
```

## Usage

### Running the Application

```bash
.venv/bin/python typewriter.py
```

The application starts in **clock mode** by default, displaying literary quotes for the current time.

### Modes

#### Clock Mode
- Automatically displays literary quotes that reference the current time
- Updates every minute with new quotes
- Press any key to switch to typewriter mode

#### Typewriter Mode
- Type on your USB typewriter keyboard
- Text appears on the e-ink display in real-time
- Special keys:
  - `Space`: Add space
  - `Enter`: New line
  - `Backspace`: Delete last character
- Type `;clock` to return to clock mode

### Testing Without Hardware

To test the clock functionality without physical hardware:
```bash
python3 test_clock_mode.py
```

## Project Structure

```
LitClockTypewriter/
├── typewriter.py           # Main application
├── literature_clock.py     # Literature clock data handler
├── working_functions.py    # Display utilities
├── test_clock_mode.py     # Testing script
├── literature/            # Literature clock CSV data
├── remington_noiseless.ttf # Typewriter font
└── requirements.txt       # Python dependencies
```

## Configuration

Key configuration variables in `typewriter.py`:

- `WIDTH`, `HEIGHT`: Display dimensions (default: 1400x1404)
- `FONTSIZE`: Text size (default: 48)
- `LINE_LENGTH`: Characters per line (default: 45)
- `SPACING`: Line spacing (default: 12)
- `FONT_FILEPATH`: Path to typewriter font

Display VCOM voltage can be adjusted on line 34:
```python
display = AutoEPDDisplay(vcom=-1.70, rotate='CCW', spi_hz=24000000)
```

## Credits

- **Literature Clock Data**: [JohannesNE/literature-clock](https://github.com/JohannesNE/literature-clock)
- **IT8951 Driver**: Based on the IT8951 e-paper display controller library
- **Font**: Remington Noiseless typewriter font

## License

MIT License - see [LICENSE](LICENSE) file for details

Copyright (c) 2019 Greg Meyer

## Troubleshooting

### Keyboard Not Detected
The application automatically searches for USB keyboard devices. If detection fails:
- Check that your USB typewriter is connected
- Verify the device appears in `evdev.list_devices()`
- Check permissions: you may need to run with `sudo` or add your user to the `input` group

### Display Issues
- Verify SPI is enabled: `ls /dev/spidev*`
- Check VCOM voltage matches your display specifications
- Adjust `spi_hz` if you experience display artifacts
- Ensure display connections are secure

### Literature Clock Data Not Loading
- Check internet connection for initial CSV download
- Verify `literature/litclock_annotated.csv` exists
- Run `python3 test_clock_mode.py` to validate data

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

Special thanks to the USB Typewriter community and e-ink display enthusiasts who make projects like this possible.
