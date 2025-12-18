"""Literature Clock Module

This module provides functionality to display time-based literary quotes
from the literature-clock project (https://github.com/JohannesNE/literature-clock).
"""

import csv
import random
import urllib.request
import os


def download_csv_data(target_path):
    """Download the literature clock CSV data from GitHub.

    Args:
        target_path: Path where the CSV file should be saved

    Raises:
        urllib.error.URLError: If download fails
    """
    url = "https://raw.githubusercontent.com/JohannesNE/literature-clock/master/litclock_annotated.csv"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    print(f"Downloading literature clock data from {url}...")

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()

        with open(target_path, 'wb') as f:
            f.write(data)

        print(f"Successfully downloaded to {target_path}")

    except urllib.error.URLError as e:
        print(f"Error downloading literature clock data: {e}")
        raise


class LiteratureClockData:
    """Manages literature clock quote data.

    Loads and indexes quotes from a pipe-delimited CSV file where each row contains:
    - Time code (HH:MM in 24-hour format)
    - Time description (natural language)
    - Quote text (literary excerpt)
    - Source metadata (title | author)
    """

    def __init__(self, csv_path):
        """Initialize and load quote data from CSV.

        Args:
            csv_path: Path to the litclock_annotated.csv file
        """
        self.quotes = {}  # Dict[str, List[Dict]]
        self._load_csv(csv_path)

    def _load_csv(self, csv_path):
        """Parse the pipe-delimited CSV and index quotes by time.

        Args:
            csv_path: Path to the CSV file
        """
        print(f"Loading literature clock data from {csv_path}...")

        quote_count = 0

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # CSV is pipe-delimited, disable quoting to handle quotes in text
                reader = csv.reader(f, delimiter='|', quoting=csv.QUOTE_NONE)

                for row in reader:
                    if len(row) < 4:
                        # Skip malformed rows
                        continue

                    time_code = row[0].strip()
                    time_natural = row[1].strip()
                    quote_text = row[2].strip()
                    source = row[3].strip()

                    # Validate time format (HH:MM)
                    if ':' not in time_code:
                        continue

                    # Store quote indexed by time
                    if time_code not in self.quotes:
                        self.quotes[time_code] = []

                    self.quotes[time_code].append({
                        'time': time_code,
                        'time_natural': time_natural,
                        'quote': quote_text,
                        'source': source
                    })

                    quote_count += 1

        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_path}")
            raise
        except Exception as e:
            print(f"Error loading CSV: {e}")
            raise

        print(f"Loaded {quote_count} quotes for {len(self.quotes)} unique times")

    def get_quote(self, hour, minute):
        """Get a random quote for the given time.

        Args:
            hour: Hour in 24-hour format (0-23)
            minute: Minute (0-59)

        Returns:
            Dict with keys: time, time_natural, quote, source
            None if no quote found for the given time
        """
        # Format time as HH:MM
        time_code = f"{hour:02d}:{minute:02d}"

        # Check if we have quotes for this time
        if time_code not in self.quotes:
            return None

        # Return random quote from available options
        quotes_for_time = self.quotes[time_code]
        return random.choice(quotes_for_time)

    def get_time_count(self):
        """Get the number of unique times with quotes.

        Returns:
            Number of unique HH:MM times that have quotes
        """
        return len(self.quotes)

    def get_total_quotes(self):
        """Get the total number of quotes across all times.

        Returns:
            Total number of quotes
        """
        return sum(len(quotes) for quotes in self.quotes.values())
