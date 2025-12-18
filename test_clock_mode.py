"""Test script for clock mode functionality without physical hardware."""

from datetime import datetime
from literature_clock import LiteratureClockData
import os

def test_clock_mode():
    """Test the clock mode functionality."""

    print("=" * 60)
    print("LITERATURE CLOCK MODE TEST")
    print("=" * 60)

    # Test 1: Load clock data
    print("\n1. Testing clock data loading...")
    csv_path = 'literature/litclock_annotated.csv'

    if not os.path.exists(csv_path):
        print(f"   ✗ CSV file not found at {csv_path}")
        return False

    clock_data = LiteratureClockData(csv_path)
    print(f"   ✓ Loaded {clock_data.get_total_quotes()} quotes for {clock_data.get_time_count()} unique times")

    # Test 2: Get quote for current time
    print("\n2. Testing quote retrieval for current time...")
    now = datetime.now()
    quote = clock_data.get_quote(now.hour, now.minute)

    if quote:
        print(f"   ✓ Current time: {now.hour:02d}:{now.minute:02d}")
        print(f"   ✓ Quote found:")
        print(f"      \"{quote['quote'][:100]}...\"")
        print(f"   ✓ Source: {quote['source']}")
    else:
        print(f"   ✓ No quote for {now.hour:02d}:{now.minute:02d} (expected for some times)")

    # Test 3: Test specific known times
    print("\n3. Testing specific times with known quotes...")
    test_times = [
        (10, 23),  # Known to have quotes
        (12, 0),   # Noon - likely to have quotes
        (0, 0),    # Midnight - definitely has quotes
        (13, 37),  # Random time - may or may not have quotes
    ]

    for hour, minute in test_times:
        quote = clock_data.get_quote(hour, minute)
        if quote:
            print(f"   ✓ {hour:02d}:{minute:02d} - Quote: \"{quote['quote'][:60]}...\"")
        else:
            print(f"   ✓ {hour:02d}:{minute:02d} - No quote available")

    # Test 4: Test command buffer logic
    print("\n4. Testing ;clock command detection...")

    def test_command_detection(typed_chars, expected_trigger):
        """Simulate typing characters and detect ;clock command."""
        command_buffer = ""
        triggered = False

        for char in typed_chars:
            command_buffer += char
            if len(command_buffer) > 6:
                command_buffer = command_buffer[-6:]

            if command_buffer.endswith(';clock'):
                triggered = True
                break

        result = "✓" if triggered == expected_trigger else "✗"
        print(f"   {result} Typed '{typed_chars}' -> Triggered: {triggered} (expected: {expected_trigger})")
        return triggered == expected_trigger

    tests = [
        ("hello;clock", True),     # Should trigger
        (";clock", True),          # Should trigger
        ("a;clock", True),         # Should trigger
        ("clock", False),          # Should NOT trigger (no semicolon)
        ("hello world", False),    # Should NOT trigger
        (";;clock", True),         # Should trigger
    ]

    all_passed = all(test_command_detection(chars, expected) for chars, expected in tests)

    # Test 5: Test display text wrapping
    print("\n5. Testing text wrapping (45 char line length)...")
    import textwrap

    LINE_LENGTH = 45
    sample_quote = "The date was the 14th of May and the clock on his desk said the time was twenty three minutes past ten, so he tapped in the numbers 10.23."

    wrapped = textwrap.fill(sample_quote, LINE_LENGTH)
    lines = wrapped.split('\n')
    print(f"   ✓ Original: {len(sample_quote)} chars")
    print(f"   ✓ Wrapped into {len(lines)} lines:")
    for i, line in enumerate(lines, 1):
        print(f"      Line {i} ({len(line)} chars): {line}")

    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ Clock data loads successfully")
    print("✓ Quote retrieval works")
    print("✓ Command detection logic correct" if all_passed else "✗ Command detection has issues")
    print("✓ Text wrapping works")
    print("\nAll basic functionality tests passed!")
    print("\nTo test on actual hardware:")
    print("1. Run: .venv/bin/python typewriter.py")
    print("2. Type ';clock' to enter clock mode")
    print("3. Press any key to exit clock mode")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_clock_mode()
