# Hardware colour sensors on Raspberry Pi Pico

Firmware (C, Pico SDK 2.2.0) that reads a dedicated colour sensor and prints
a colour name plus the measurements it was derived from over USB serial.
Each sensor has its own self-contained project folder that can be opened
directly in VS Code with the Raspberry Pi Pico extension.

| Folder | Sensor | Interface | Board | Programs |
| --- | --- | --- | --- | --- |
| `tcs3200/` | TCS3200 / TCS230 | Frequency output on one GPIO | Pico (RP2040) | `tcs3200_classify` |
| `tcs3472/` | TCS3472x family | I2C, address 0x29 | Pico (RP2040) | `tcs3472_classify` |
| `tcs34725/` | TCS34725 | I2C, address 0x29 | Pico 2 W (RP2350) | `tcs34725_raw`, `tcs34725_classify` |

The TCS34725 is a member of the TCS3472x family, so the `tcs3472` and
`tcs34725` programs share the same register map and nearly identical code.
They are kept separate because they target different boards; the `tcs3472`
version also waits for the data-valid flag and handles I2C read errors.

## Wiring

### TCS3200 (`tcs3200/`)

| Sensor pin | Pico GPIO | Purpose |
| --- | --- | --- |
| S0 | GP2 | Output frequency scaling (held at 20 %) |
| S1 | GP3 | |
| S2 | GP4 | Photodiode filter select |
| S3 | GP5 | |
| OUT | GP6 | Square wave; rising edges are counted by interrupt |
| VCC | 3V3 | |
| GND | GND | |
| OE | GND | Only if your module exposes it (active-low enable) |

Pins are `#define`d at the top of `tcs3200_classify.c`.

### TCS3472x / TCS34725 (`tcs3472/`, `tcs34725/`)

| Sensor pin | Pico pin | Notes |
| --- | --- | --- |
| SDA | GP4 | I2C0 |
| SCL | GP5 | I2C0 |
| VIN | 3V3 | |
| GND | GND | |
| LED | GND (optional) | Grounding it turns the breakout's white LED off |

At boot the chip ID is printed. Expect `0x44` (TCS34721/5) or `0x4D`
(TCS34723/7). Anything else, or an init failure, means a wiring problem.

## Building and flashing

### VS Code (recommended)

Open the sensor folder (for example `color-sensors/tcs34725/`) as the
workspace. The bundled `.vscode/` settings point at the SDK installed by
the extension under `~/.pico-sdk`. Use the extension's **Compile Project**
task, then **Run Project** with the board in BOOTSEL mode, or **Flash** if
a debug probe is attached.

### Command line

The Pico extension installs CMake, Ninja and the ARM toolchain under
`~/.pico-sdk`; the snippet below reuses them.

```bash
export PICO_SDK_PATH=~/.pico-sdk/sdk/2.2.0
export PICO_TOOLCHAIN_PATH=~/.pico-sdk/toolchain/14_2_Rel1
export PATH=~/.pico-sdk/toolchain/14_2_Rel1/bin:~/.pico-sdk/cmake/v3.31.5/bin:~/.pico-sdk/ninja/v1.12.1:$PATH

cd color-sensors/tcs34725
cmake -S . -B build -G Ninja
ninja -C build
```

Hold BOOTSEL while plugging in the board and copy the `.uf2` from `build/`
onto the mounted drive. To build for a different board, change
`PICO_BOARD` in that folder's `CMakeLists.txt` (`pico`, `pico_w`, `pico2`,
`pico2_w`).

## Reading the output

Connect to the board's USB serial port (115200 baud; the VS Code Serial
Monitor extension works). Classifier programs print one line per sample:

```
GREEN   | C:812 R:190 G:402 B:155 | rn:0.23 gn:0.50 bn:0.19
```

- `C R G B` are the raw readings: pulse frequency in Hz for the TCS3200,
  16-bit counts for the I2C sensors.
- `rn gn bn` are each channel divided by clear. Normalising by clear makes
  the ratios largely independent of brightness and distance, which is what
  the classifier thresholds on.

`tcs34725_raw` prints only `C R G B`; use it to confirm wiring before
flashing the classifier.

## How the classifier works

`classify_color()` is the same heuristic in all three classifier programs:

1. Very low clear reading means nothing reflective is in front of the sensor,
   so return `BLACK`.
2. Compute the normalised ratios and their spread (`max - min`, a rough
   saturation). Low spread means a neutral colour: `BLACK`, `WHITE` or
   `GRAY` depending on the clear level.
3. Check `BROWN` (red-dominant but dim, blue low) before the saturated
   colours, since it would otherwise be caught by the red rule.
4. Pick the dominant channel: `RED` (with `ORANGE` and, for the I2C sensors,
   `PINK` sub-cases), `GREEN`, `BLUE`.
5. Fall back to two-channel mixes `YELLOW` and `PURPLE`, else `UNKNOWN`.

The thresholds were tuned by hand for one setup. To retune, hold reference
objects at the working distance, watch the `rn/gn/bn` ratios and clear
values on the serial monitor, and adjust the constants in `classify_color()`.
The absolute clear thresholds (for black/white decisions) depend on gain,
integration time and ambient light, so expect to change those first.

## Project files

Each folder contains the standard Pico VS Code project scaffolding:

- `CMakeLists.txt` - board selection, target(s), USB stdio enabled.
- `pico_sdk_import.cmake` - locates the SDK via `PICO_SDK_PATH` (unmodified SDK boilerplate).
- `.vscode/` - extension settings, build tasks and debug launch configs.
- `build/` - generated output, ignored by git.
