# Minai Printer — Hardware Specification (v0.2 draft)

Status: draft for review, then for RFQ (request for quotation) to a manufacturer.
First order: 100 units. A reference schematic and board layout that implement
this specification are in [`hardware/`](../hardware/README.md).
All prices are estimates to be replaced by real quotes. Items marked **[confirm]**
depend on the datasheet of the mechanism the supplier actually sources.

## 1. Product in one paragraph

A small Wi-Fi receipt printer that AI agents and scripts can print to. It takes
58 mm thermal paper, is powered by any USB-C charger, and has one button and one
light. It contains no fonts, no layout engine and no printer language: it
receives a 384-pixel-wide black-and-white image and prints it. Everything smart
happens in software upstream, which is what keeps the hardware cheap.

## 2. Design principles

| Principle | Consequence for hardware |
|---|---|
| Cheapest possible | Commodity 58 mm mechanism, one small 2-layer PCB, one pre-certified radio module, no battery, no cutter, no display |
| Dumb device, smart cloud | Raster-only printing; small MCU and 4 MB flash are enough |
| Reachable by agents | Wi-Fi on board; the device dials out to a server, so it works behind home routers |
| Human in the loop | One large button (acknowledge / reprint / "print my briefing") and one status LED |
| Buildable by a third party | Only standard parts with multiple sources; nothing needing custom silicon or exotic processes |

## 3. Requirements

### 3.1 Printing

| Item | Requirement |
|---|---|
| Technology | Direct thermal, line head |
| Paper | 57–58 mm wide thermal roll, outer diameter up to 40 mm, paper 55–80 µm |
| Printable width | 48 mm, 384 dots per line |
| Resolution | 8 dots/mm (203 dpi) |
| Speed | ≥ 25 mm/s on typical text at 5 V; ≥ 10 mm/s on solid black |
| Paper loading | Drop-in ("clamshell"): open lid, drop roll, close lid |
| Paper cutting | Serrated tear bar on the lid; no motorised cutter (decided) |
| Sensors | Paper-out sensor (reflective optical, part of mechanism), head thermistor (part of head), lid-open detection optional |
| Mechanism life | Per mechanism datasheet, typically 50 km of paper **[confirm]** |

### 3.2 Compute and connectivity

| Item | Requirement |
|---|---|
| MCU / radio | Espressif ESP32-C3-WROOM-02 module, 4 MB flash (pre-certified radio module) |
| Wireless | Wi-Fi 802.11 b/g/n 2.4 GHz; Bluetooth LE 5 (used for first-time Wi-Fi setup) |
| Wired | USB-C: power, firmware flashing, and USB serial printing (native USB of the ESP32-C3) |
| Firmware update | Over the air, with a rollback partition |
| Alternative modules | ESP32-C3-MINI-1 (smaller, same chip) or ESP32-C6 (more pins) if the supplier prefers |

### 3.3 User interface

| Item | Requirement |
|---|---|
| Button | One tactile switch behind a large keycap. Also serves as the boot/flash button |
| LED | One RGB LED (WS2812-type, single data pin) behind a light pipe or thin wall |
| Sound | None |

### 3.4 Power

| Item | Requirement |
|---|---|
| Input | USB-C receptacle, 5 V, with 5.1 kΩ pull-downs on CC1 and CC2 |
| Supply needed | 5 V / 2 A or better charger. Must still work, slower, on weaker ports |
| Head voltage (VH) | 5 V rail through a switch, straight to the head. No boost converter |
| Logic | 3.3 V from a 600 mA regulator |
| Idle power | < 0.5 W with Wi-Fi connected |
| Battery | None (decided) |

### 3.5 Mechanical and environmental

| Item | Requirement |
|---|---|
| Size target | ≤ 80 × 100 × 55 mm. Reference main board is 62 × 49 mm |
| Enclosure, first 100 units | 3D printed (MJF or SLS nylon), 2 main parts plus lid and button, 2–4 screws |
| Enclosure, volume | Same geometry, injection-moulded ABS once the design is proven |
| Operating range | 5–40 °C, indoor |
| Compliance targets | FCC Part 15, CE (RED), RoHS, REACH. Use the module's existing radio certification |

## 4. Reference architecture

```
 USB-C 5V ──┬── 3.3V regulator ── ESP32-C3-MINI-1 ── button, RGB LED
            │                        │  │  │
            │        SPI data/clock/latch  │  └─ ADC: head thermistor, paper sensor
            │                        │  strobe ×2
            ├── VH switch (P-FET) ───┴──────► thermal head (384 dots)
            │        ▲ enable
            ├── bulk capacitors (≥ 2000 µF)
            └── stepper driver (dual H-bridge + inverter) ──► paper feed motor
```

The print mechanism is a bare 58 mm unit of the PT486F family (Xiamen PRT),
interchangeable with Fujitsu FTP-628MCL101, Seiko LTPZ245 and APS FM205. It
includes the head, the stepper motor, the paper sensor and the platen roller.
It is driven directly by the MCU; there is no separate printer controller board.

## 5. Electrical design notes

### 5.1 Thermal head

- Interface: serial data in, clock, latch, strobe lines (usually 6, each firing
  64 dots), thermistor, VH and logic supply. Logic levels are 3.3 V compatible **[confirm]**.
- Head voltage range for this family is typically 4.2–8.5 V **[confirm]**, so 5 V direct works.
- The 6 strobes are wired as 2 groups of 3 to save MCU pins.
- Each dot draws roughly 30–40 mA at 5 V **[confirm from head resistance]**.
  Firing a whole line at once would draw over 10 A, so firmware splits each line
  into passes of at most ~48 dots, keeping peak current under about 2 A.

### 5.2 Head protection (must-have)

A strobe line stuck active will burn the head in under a second.

- Pull resistors on every strobe line so the head is off while the MCU is in reset or booting.
- VH goes through a P-channel MOSFET that is off by default and enabled by firmware only while printing.
- Firmware: watchdog timer, maximum strobe time, over-temperature cut-off using the head thermistor (stop at about 65 °C).
- Supplier to propose a hardware strobe time-out (monostable) if it adds less than $0.05.

### 5.3 Power integrity

- At least 2000 µF low-ESR capacitance on VH, close to the head connector.
- The 3.3 V regulator input must be isolated from VH dips (series diode or small
  resistor plus its own 100 µF capacitor) so head pulses cannot reset the MCU.
- ESD protection diodes on USB data lines; a resettable fuse or current-limit switch on the 5 V input.

### 5.4 Pin budget

The ESP32-C3 module has 13 usable GPIOs once the 2 USB pins are reserved, and
the design uses all of them: head clock, data, latch, 2 strobe groups, 2 motor
phases, head-power enable, thermistor, paper sensor, head-voltage sense,
button and LED. The motor is driven from 2 pins by a DRV8833 H-bridge with a
dual inverter generating the complementary inputs. The full pin map is in
[`hardware/README.md`](../hardware/README.md).

### 5.5 PCB

- 2 layers, 1.6 mm FR-4, 62 × 49 mm in the reference layout, all parts on one side.
- FPC connector matching the mechanism's flex cable.
- Test pads for 5 V, 3.3 V, GND, head power, reset and head data-out.

## 6. Cost estimate (per unit, ex-works)

| Item | 100 units | 1,000 units |
|---|---|---|
| 58 mm print mechanism | 5.50 | 4.20 |
| ESP32-C3 module | 2.50 | 1.90 |
| Other electronic parts | 2.50 | 1.50 |
| PCB and assembly (including set-up share) | 4.00 | 1.15 |
| Enclosure (3D printed at 100; moulded at 1,000) | 7.00 | 1.20 |
| USB-C cable and starter paper roll | 1.00 | 0.70 |
| Packaging | 1.00 | 0.50 |
| Final assembly and test | 3.00 | 1.00 |
| **Total, USD** | **≈ 26** | **≈ 12** |

All figures are estimates to be replaced by quotes. The only one checked
against a current listing is the mechanism ($3.90–4.50 in volume).

One-time costs on top: supplier engineering fees, and compliance testing
(roughly $3,000–8,000 with a pre-certified module) if the 100 units are sold
rather than used as a private pilot. Injection-mould tooling (roughly
$4,000–8,000) is deferred until after the first 100.

## 7. Build plan

| Stage | Units | What is built | Purpose |
|---|---|---|---|
| P0 bench | 1–2 | Dev board + off-the-shelf 58 mm serial printer module | Start firmware and cloud software immediately |
| P1 prototype | 5–10 | Reference PCB after engineer review, bare mechanism, 3D-printed case | Prove direct head drive, power on 5 V, print quality |
| P2 first order | 100 | Revised PCB, 3D-printed case, factory test | Real users, compliance pre-scan |
| P3 volume | 1,000+ | Moulded enclosure, test fixture | Only if P2 justifies it |

Two ways to get it made:

1. **Custom build** as specified here: a PCB assembler for P1, then a contract manufacturer for P2–P3.
2. **Adapt an existing product**: ask a factory that already makes 58 mm
   printers to fit our PCB (or our firmware on their ESP32 board) into their
   existing enclosure. This skips tooling cost and is usually the cheapest and
   fastest route to the first batch. Recommended to quote both.

## 8. Factory acceptance test (every unit)

1. Power on from a 5 V / 2 A supply; idle current within limit.
2. Flash firmware and write serial number over USB.
3. Print the test pattern: all 384 dots, checkerboard, solid black bar, fine text. No missing dots, no MCU reset during the black bar.
4. Paper-out sensor reads correctly with and without paper.
5. Thermistor reads room temperature ± 5 °C.
6. Button press and all three LED colours verified.
7. Wi-Fi signal strength above threshold against a reference access point.

## 9. What to ask the supplier for

- Unit price at 100, 1,000 and 5,000 units, with a costed bill of materials.
- One-time costs: engineering, tooling, test fixture, certification.
- Datasheet of the exact print mechanism proposed (voltage range, dot resistance, connector pinout, life).
- Schematic and PCB files as deliverables owned by us.
- Lead time for 10 prototypes and for the first production batch.
- Their proposal for anything in this document they would change to cut cost.

## 10. Decisions

| Decision | Outcome |
|---|---|
| Battery | None |
| Cutter | Tear bar |
| First order size | 100 units |
| Paper width | 58 mm |
| Extra inputs (microphone, NFC, more buttons) | Not in this version |

## Sources

- PT486F compatibility with FTP-628MCL101 / LTPZ245 / FM205: https://www.edaboard.com/threads/theraml-printer-mechanism-from-china.154194/
- Mechanism price range: https://china.org.ru/product/1600620307316
- Voltage range of a comparable 2-inch mechanism (Seiko LTPH245D-C384, 4.2–8.5 V): https://masterelectronics.com/en/seiko-instruments/ltph245dc384e-12409282.html
