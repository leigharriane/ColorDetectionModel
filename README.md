# ColorDetectionModel

Colour-based waste sorting experiments. An object is classified by its
dominant colour and mapped to a bin: green and blue are treated as
**Recycle**, while black, brown and grey are treated as **Garbage**.

Two independent approaches live in this repo:

| Folder | Hardware | Language | What it does |
| --- | --- | --- | --- |
| [`camera/`](camera/) | Any webcam + a computer | Python 3 / OpenCV | HSV thresholding of a live video feed, with a multi-object mode and a single-zone "sorting station" mode |
| [`color-sensors/`](color-sensors/) | Raspberry Pi Pico + TCS3200 / TCS3472 / TCS34725 sensor | C (Pico SDK 2.2.0) | Reads a hardware colour sensor and prints a colour name over USB serial |

Each folder has its own README with setup, wiring and tuning notes.

## Quick start

Camera (needs Python 3.10+):

```bash
cd camera
pip install -r requirements.txt
python detect_zone.py          # hold an item in the centre box, read one answer
python detect_multicolor.py    # box every matching region in the frame
python hsv_tuner.py --preset black   # find/adjust HSV thresholds
```

Pico firmware: open one of the `color-sensors/<sensor>/` folders in VS Code
with the Raspberry Pi Pico extension and press *Compile* / *Run*, or build
from the command line as described in [`color-sensors/README.md`](color-sensors/README.md).

## Repository layout

```
camera/
  color_ranges.py          HSV thresholds + Recycle/Garbage mapping (single source of truth)
  common.py                shared CLI flags, camera open, mask clean-up
  detect_multicolor.py     box every colour region in the whole frame
  detect_zone.py           one decision for the object inside a centre box
  hsv_tuner.py             trackbar tool for calibrating thresholds
  legacy/                  first tutorial-derived version, kept for reference
color-sensors/
  tcs3200/                 frequency-output sensor, Pico (RP2040)
  tcs3472/                 I2C sensor, Pico (RP2040)
  tcs34725/                I2C sensor, Pico 2 W; raw-dump and classifier programs
```

## History of the file layout

The repository was reorganised in November 2026. Earlier versions of each
script are still in git history; this table maps old names to new ones.

| Old path | Now |
| --- | --- |
| `camera-module/detection.py`, `detectionv2.py` | `camera/detect_multicolor.py` (`--profile original` / `tuned`) |
| `camera-module/area-detection.py`, `area-detectionv2.py`, `area-detectionv3.py` | `camera/detect_zone.py` (`--profile original` / `tuned`) |
| `camera-module/reader.py`, `color-specific/black.py` | `camera/hsv_tuner.py` (`--preset black` reproduces the second) |
| `camera-module/color.py` | `camera/legacy/multicolor_original.py` |
| `color-sensors/TCS3200/test-tcs3200/test-tcs3200.c` | `color-sensors/tcs3200/tcs3200_classify.c` |
| `color-sensors/TCS3472/test-tcs3472/test-tcs3472.c` | `color-sensors/tcs3472/tcs3472_classify.c` |
| `color-sensors/TCS34725/test/test.c`, `color.c` | `color-sensors/tcs34725/tcs34725_raw.c`, `tcs34725_classify.c` |

The "v2"/"v3" scripts differed from their predecessors only in HSV
thresholds. Those two threshold sets are now the `original` and `tuned`
profiles in `camera/color_ranges.py`.
