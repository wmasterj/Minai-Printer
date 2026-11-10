# Minai Printer

A very cheap Wi-Fi receipt printer built for AI agents to print to.

The device is deliberately dumb: it receives a 384-pixel-wide black-and-white
image over Wi-Fi or USB and prints it on 58 mm thermal paper. Layout, fonts and
intelligence live in software upstream.

- Target build cost: about $26 per unit for the first 100, about $12 at 1,000 (estimates)
- Power: any USB-C charger, no battery
- Interface: one button, one light

## Documents

- [Hardware specification](docs/hardware-spec.md) — requirements, reference
  architecture, cost estimate, build plan, and what to ask a manufacturer for.

- [Reference design](hardware/README.md) — schematic, routed board, gerbers
  and parts list with links for the main circuit board.

- [Enclosure](hardware/enclosure/README.md) — 3D model of the case, with
  STEP and STL files for the four printed parts.

## Status

Specification and a first-pass reference board design, checked in software
only, plus a concept enclosure. Nothing has been built. No firmware yet.
