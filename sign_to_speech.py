import argparse
import logging
import sys
import time

import pyttsx3
import serial
import serial.tools.list_ports


def setup_logging(log_file='sign_to_speech.log', log_level='INFO'):
    """Setup logging with both file and console handlers."""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    file_level = level_map.get(log_level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(file_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Could not setup file logging: {exc}")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(file_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Logging configured successfully")


class GestureDebouncer:
    """Prevents rapid repetition of the same gesture."""

    def __init__(self, delay=2.0):
        self.delay = delay
        self.last_time = {}
        logging.info("GestureDebouncer initialized with %.1fs delay", delay)

    def should_speak(self, gesture):
        current_time = time.time()

        if gesture not in self.last_time:
            self.last_time[gesture] = current_time
            return True

        time_elapsed = current_time - self.last_time[gesture]
        if time_elapsed > self.delay:
            self.last_time[gesture] = current_time
            return True

        logging.debug(
            "Gesture '%s' debounced (%.1fs < %.1fs)", gesture, time_elapsed, self.delay
        )
        return False


def find_arduino_port():
    """Automatically detect Arduino-like serial ports."""
    ports = serial.tools.list_ports.comports()
    arduino_keywords = ['Arduino', 'CH340', 'CP210', 'FTDI', 'USB Serial']

    for port in ports:
        description_upper = port.description.upper()
        for keyword in arduino_keywords:
            if keyword.upper() in description_upper:
                logging.info("Arduino detected: %s (%s)", port.device, port.description)
                return port.device

    logging.warning("No Arduino port detected automatically")
    return None


def list_available_ports():
    """List all available serial ports."""
    print("\n" + "=" * 60)
    print("Available Serial Ports:")
    print("=" * 60)

    ports = serial.tools.list_ports.comports()

    if ports:
        for port in ports:
            print(f"\nPort: {port.device}")
            print(f"  Description: {port.description}")
            print(f"  Hardware ID: {port.hwid}")
    else:
        print("\nNo serial ports found")

    print("\n" + "=" * 60 + "\n")


def configure_tts(engine):
    """Log TTS properties and return configured engine."""
    logging.info("TTS Engine configured successfully")
    logging.info("Speech rate: %s WPM", engine.getProperty('rate'))
    logging.info("Volume: %s", engine.getProperty('volume'))
    return engine


def init_serial(port, baudrate=9600, timeout=1):
    """Initialize serial communication."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)
        logging.info("Serial connection established on %s at %s baud", port, baudrate)
        return ser
    except serial.SerialException as exc:
        logging.error("Error opening serial port %s: %s", port, exc)
        return None


def text_to_speech(text, engine):
    """Convert text to speech."""
    if text and text.strip():
        logging.info("Speaking: %s", text)
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            logging.error("TTS error: %s", exc)


def list_tts_voices():
    """List all available TTS voices."""
    print("\nInitializing TTS engine to detect voices...\n")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    if not voices:
        print("No voices available")
        return

    print(f"{'=' * 60}")
    print(f"Available Voices ({len(voices)} found):")
    print(f"{'=' * 60}")

    for i, voice in enumerate(voices):
        print(f"\nVoice {i}:")
        print(f"  Name: {voice.name}")
        print(f"  ID: {voice.id}")
        print(f"  Languages: {getattr(voice, 'languages', 'N/A')}")

    print(f"\n{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Sign Language to Speech Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--port', default=None)
    parser.add_argument('--baudrate', type=int, default=9600)
    parser.add_argument('--mode', choices=['direct', 'mapped'], default='direct')
    parser.add_argument('--debounce', type=float, default=2.0)
    parser.add_argument('--rate', type=int, default=150)
    parser.add_argument('--volume', type=float, default=1.0)
    parser.add_argument('--list-ports', action='store_true')
    parser.add_argument('--list-voices', action='store_true')
    parser.add_argument(
        '--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO'
    )
    parser.add_argument('--log-file', default='sign_to_speech.log')
    args = parser.parse_args()

    setup_logging(log_file=args.log_file, log_level=args.log_level)

    if args.list_ports:
        list_available_ports()
        return 0
    if args.list_voices:
        list_tts_voices()
        return 0

    if not 0.0 <= args.volume <= 1.0:
        print("Error: Volume must be between 0.0 and 1.0")
        return 1
    if args.debounce < 0:
        print("Error: Debounce delay must be positive")
        return 1

    engine = pyttsx3.init()
    engine.setProperty('rate', args.rate)
    engine.setProperty('volume', args.volume)
    configure_tts(engine)

    debouncer = GestureDebouncer(delay=args.debounce)

    gesture_map = {
        '0': 'Hello',
        '1': 'Thank you',
        '2': 'Please',
        '3': 'Yes',
        '4': 'No',
        '5': 'Help',
        '6': 'Water',
        '7': 'Food',
        '8': 'Bathroom',
        '9': 'Goodbye',
    }

    serial_port = args.port or find_arduino_port()
    if serial_port is None:
        print("Error: Could not auto-detect Arduino. Please specify --port")
        return 1

    ser = init_serial(serial_port, args.baudrate)
    if ser is None:
        print("Failed to establish serial connection. Exiting...")
        return 1

    print("\n" + "=" * 60)
    print(f"  Sign to Speech Converter ({args.mode.upper()} mode)")
    print("=" * 60)

    if args.mode == 'mapped':
        print("\nGesture Mappings:")
        for gesture in sorted(gesture_map.keys()):
            print(f"  {gesture:>3} -> {gesture_map[gesture]}")

    print(f"\nListening on: {serial_port}")
    print(f"Baud rate: {args.baudrate}")
    print(f"Debounce delay: {args.debounce}s")
    print(f"Speech rate: {args.rate} WPM")
    print(f"Volume: {args.volume}")
    print("\nPress Ctrl+C to exit\n")

    try:
        while True:
            if ser.in_waiting > 0:
                try:
                    data = ser.readline().decode('utf-8').strip()
                    if data and debouncer.should_speak(data):
                        if args.mode == 'mapped':
                            if data in gesture_map:
                                text = gesture_map[data]
                                logging.info("Gesture: %s -> %s", data, text)
                                text_to_speech(text, engine)
                            else:
                                logging.warning("Unknown gesture: %s", data)
                        else:
                            text_to_speech(data, engine)
                except UnicodeDecodeError:
                    logging.warning("Error decoding data - skipping")
                except Exception as exc:
                    logging.error("Error in main loop: %s", exc)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
        logging.info("Program interrupted by user")
    finally:
        if ser and ser.is_open:
            ser.close()
            logging.info("Serial connection closed")

        try:
            engine.stop()
            logging.info("TTS engine stopped")
        except Exception:
            pass

        print("Program terminated successfully")

    return 0


if __name__ == '__main__':
    sys.exit(main())
