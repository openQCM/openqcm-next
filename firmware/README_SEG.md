# Segmented-sweep firmware (experimental, branch impedance-analysis-sweep-adaptive)

The adaptive sweep (`docs/impedance-analysis/ADAPTIVE_SWEEP.md`) needs the command

    Z<start>;<stop>;<step>;<dwell_us>[;<start>;<stop>;<step>;<dwell_us>...]

It takes up to 8 segments, swept in the order given, each from start to stop included: upwards
with step > 0, downwards with step < 0. Each point waits dwell_us (0–100 000) more, then is measured
and printed as in the plain sweep. The usual end-of-measurement line follows. `Q` stops it. A
malformed command answers `ERR_SEG` and the end line: since 2026-10-26 also a field that is not a
whole number (`atol` had read it as 0) or a start or stop outside 1 Hz–60 MHz (both images rebuilt,
same version; from openQCM Lab's review of its PR #2). Everything else is unchanged.

| Folder | Version | Based on | For |
|---|---|---|---|
| `openQCM_Next_py_0.1.5d_SEG_teensy/` | `0.1.5d-SEG` | `0.1.5d` | the Next with TEC |
| `openQCM_Next_py_0.1.5d_SEG_TEST_teensy/` | `0.1.5d-SEG-TEST` | `0.1.5d-TEST` | no-TEC boards, and an openQCM Q-1 used as a bench board |

The `-TEST` variant also reads the board's **MCP9808** when it has one (the Q-1 does), at every end
of measurement, as the Q-1 firmware does. Without one, it reports a constant 25.00 °C (the 0.05 °C
wobble is off).

**Built** on 2026-10-25, rebuilt on 2026-10-26, with the Arduino IDE's arduino-cli, Teensy core 1.59:

    arduino-cli compile --fqbn teensy:avr:teensy40:usb=serial,speed=600 <folder>

The `.hex` files are in each folder and in `software/openQCM/firmware_update/`.

**Flash** with `teensy_loader_cli --mcu=TEENSY40 -w -v <hex>`, then open the port at 134 baud to
reboot the board into the loader.

**Back to the originals:** the 0.1.5d and 0.1.5d-TEST images in `firmware_update/`.
