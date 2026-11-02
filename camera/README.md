# Camera-based colour detection

Python scripts that classify objects in a webcam feed by colour using
OpenCV HSV thresholding. Detected colours are mapped to a waste category:
green and blue to **Recycle**, black, brown and grey to **Garbage**.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
```

Requires Python 3.10 or newer. Every script accepts `--camera N` to pick a
different OpenCV camera index (default 0) and `--profile` to pick a
threshold set (see below). Press `q` in any video window to quit.

## Scripts

| Script | Use it when | Output |
| --- | --- | --- |
| `detect_zone.py` | You want **one answer** for an object held in the centre of the frame (sorting-station mode) | White centre box; banner `COLOUR -> Category (coverage %)` or `Unknown`; box around the winning blob |
| `detect_multicolor.py` | You want to see **every** colour region in the whole frame at once | A labelled box per matching blob, any number of colours |
| `hsv_tuner.py` | You need to **calibrate** a colour's HSV range for your lighting | Trackbars plus Frame/Mask/Result windows; prints bounds with `p` or on exit |

### detect_zone.py

```bash
python detect_zone.py [--roi 200 200] [--min-coverage 0.15] [--min-area 300]
```

For each colour in the profile the script computes *coverage*: the fraction
of pixels inside the region of interest (ROI) that match that colour's HSV
window. The colour with the highest coverage wins if it is at least
`--min-coverage` (default 15 %). The largest blob of the winning colour is
boxed when it is at least `--min-area` pixels.

### detect_multicolor.py

```bash
python detect_multicolor.py [--min-area 300]
```

Runs every colour's mask over the full frame independently and boxes each
contour larger than `--min-area`. Overlapping windows (for example the
`tuned` blue range, see below) will produce overlapping boxes.

### hsv_tuner.py

```bash
python hsv_tuner.py                 # start from the full HSV range
python hsv_tuner.py --preset black  # start from black's current range
```

Drag the six trackbars (lower/upper H, S, V) until the Mask window shows
only the target object. Press `p` to print the bounds, then paste them
into the matching `ColorRange` in `color_ranges.py`.

## Threshold profiles (`color_ranges.py`)

All HSV ranges live in one file. OpenCV HSV uses hue 0-179 and
saturation/value 0-255.

| Colour | Category | `original` lower / upper | `tuned` lower / upper (default) |
| --- | --- | --- | --- |
| green | Recycle | (25, 56, 75) / (102, 255, 255) | same |
| blue | Recycle | (93, 134, 7) / (144, 255, 255) | (86, 0, 0) / (179, 255, 255) |
| black | Garbage | (0, 0, 0) / (180, 255, 40) | (0, 0, 0) / (179, 80, 80) |
| brown | Garbage | (7, 60, 30) / (70, 255, 255) | same |
| grey | Garbage | (0, 0, 0) / (180, 50, 200) | (0, 0, 83) / (179, 50, 180) |

`original` is the first hand-tuned set. `tuned` is the later re-tune that
the most recent scripts used, so it is the default. Select either with
`--profile`.

Caveat on `tuned` blue: it accepts any hue from 86 up with **no saturation
or value floor**, so it also matches white, light grey and very dark
pixels. In zone mode this is partly masked because the highest coverage
wins, but in multi-colour mode neutral objects will often be boxed as
blue. Raise the saturation floor (second value of `lower`) if that is a
problem in your setup.

The windows also overlap each other in places. Brown (hue 7-70) sits inside
green's hue span (25-102), so a saturated green object is usually boxed as
both green and brown in multi-colour mode. Zone mode is unaffected because
only the colour with the most coverage is reported.

## How detection works

1. Convert the BGR frame (or just the ROI) to HSV.
2. `cv2.inRange` with a colour's lower/upper bounds gives a binary mask.
3. The mask is opened with a 5x5 kernel to drop speckle, then dilated to
   re-grow the surviving blobs (`common.color_mask`).
4. `cv2.findContours` finds blobs; small ones are discarded by area.
5. Either every blob is boxed (multi-colour) or coverage is compared
   across colours and only the winner is reported (zone).

## Module layout

- `color_ranges.py` - `ColorRange` dataclass, the `PROFILES` table, `get_profile()`.
- `common.py` - shared CLI flags, `open_camera`, `frames`, `color_mask`, `put_label`.
- `detect_zone.py` - `centered_roi`, `classify_roi`, `annotate_frame`, `main`.
- `detect_multicolor.py` - `draw_detections`, `annotate_frame`, `main`.
- `hsv_tuner.py` - trackbar helpers and the tuning loop.
- `legacy/multicolor_original.py` - the first tutorial-derived script; not imported anywhere.

The `annotate_frame` functions take a frame and return a result without
touching the camera, so they can be tested on still images.
