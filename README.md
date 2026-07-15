# openQCM NEXT — monorepo (software + firmware + docs)

Python desktop application (PyQt5) for data acquisition from the openQCM NEXT
quartz crystal microbalance (QCM), based on a Teensy 4.0 microcontroller and an
AD8302 gain/phase detector.

This repository is a **reconstruction of the development history** from separate
per-version folders. The chronology is expressed through commits and tags; commit
dates are those of the reconstruction (the original file timestamps are unreliable).

## Layout

| Folder | Content |
|---|---|
| `software/` | Python application (`openQCM` package). Evolves across history. |
| `firmware/` | Teensy 4.0 firmware source (`.ino` + `src/`). |
| `research/` | Development materials: peak-detection prototypes, notes. |
| `docs/impedance-analysis/` | Impedance-analysis method docs (on the `impedance-analysis` branch). |

## Versions (tags)

| Tag | Description | Branch |
|---|---|---|
| `v0.1.5` | Production baseline | `main` |
| `v0.1.6-dev` | Automatic peak detection, TEC current monitoring, dark UI + real-time plot | `main` |
| `v0.1.6-dev-073` | Add-On menu GUI, I/O robustness, firmware 0.1.5a | `main` |
| `v0.1.6G-test` | Impedance analysis via conductance spectrum (experimental) | `impedance-analysis` |

## Running

```
cd software && python app.py      # or: python -m openQCM
```

Main dependencies: `numpy scipy pyserial pyqtgraph matplotlib pandas PyQt5`
(see roadmap: a `requirements.txt` is currently missing).

## Firmware

The Teensy firmware is common to all software versions at the serial-protocol
level (USB-CDC 115200 8N1). Versions `0.1.5` and `0.1.5a` differ only in the
analog amplifier gain (`POT_VALUE`), not in the protocol.

## License

The code is distributed under the **GPL** (see `software/openQCM/docs/`).
