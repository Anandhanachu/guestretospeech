# Sign to Speech (Python + Arduino)

This repo includes:

- `sign_to_speech.py`: Python listener that reads serial data from Arduino and speaks it using TTS.
- `arduino/sign_to_speech_sender/sign_to_speech_sender.ino`: Arduino sketch for **5 flex sensors** that sends gesture IDs (`0`-`9`) using finger-combination patterns.

## Python setup

```bash
pip install pyserial pyttsx3
python sign_to_speech.py --mode mapped
```

Useful commands:

```bash
python sign_to_speech.py --list-ports
python sign_to_speech.py --list-voices
python sign_to_speech.py --port /dev/ttyUSB0 --mode mapped --debounce 2.0
```

## Arduino wiring (5 flex sensors)

- Connect flex sensors to analog pins:
  - Thumb  -> `A0`
  - Index  -> `A1`
  - Middle -> `A2`
  - Ring   -> `A3`
  - Pinky  -> `A4`
- Use a proper voltage divider for each flex sensor so Arduino reads analog bend values.
- In the sketch, calibrate:
  - `FLEX_THRESHOLD[]`
  - `INVERT_BENT_LOGIC[]`

## Combination mapping used by Arduino

The Arduino builds a 5-bit finger mask (`thumb..pinky`) and maps known combinations to IDs:

- `00001` -> `0`
- `00010` -> `1`
- `00100` -> `2`
- `01000` -> `3`
- `10000` -> `4`
- `00011` -> `5`
- `00110` -> `6`
- `01100` -> `7`
- `11000` -> `8`
- `11111` -> `9`

In Python `--mode mapped`, IDs map to words like Hello, Thank you, Please, etc.
