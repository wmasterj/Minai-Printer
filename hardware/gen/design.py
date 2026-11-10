"""Single source of truth for the Minai Printer reference design.

Every part is listed once with its schematic symbol, footprint, pin-to-net
map, schematic position and board position. gen_sch.py and gen_pcb.py both
read this file, so the schematic and the board cannot disagree.

Schematic positions are in units of 2.54 mm. Board positions are in mm from
the top-left board corner; rotation in degrees (KiCad convention).
"""

BOARD_W, BOARD_H = 62.0, 49.0

R0603 = "Resistor_SMD:R_0603_1608Metric"
R0805 = "Resistor_SMD:R_0805_2012Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
TP = "TestPoint:TestPoint_Pad_D1.5mm"
HOLE = "MountingHole:MountingHole_2.2mm_M2"

PARTS = []


def P(ref, lib, value, fp, nets, sch, pcb, rot=0, mpn="", mfr="", desc="", **kw):
    PARTS.append(dict(ref=ref, lib=lib, value=value, fp=fp, nets=nets, sch=sch,
                      pcb=pcb, rot=rot, mpn=mpn, mfr=mfr, desc=desc, **kw))


def R(ref, value, a, b, sch, pcb, fp=R0603, rot=0, **kw):
    P(ref, "Device:R", value, fp, {"1": a, "2": b}, sch, pcb, rot,
      desc=kw.pop("desc", "Resistor %s %s" % (value, fp.split(":")[1].split("_")[1])), **kw)


def C(ref, value, a, b, sch, pcb, fp=C0603, rot=0, **kw):
    P(ref, "Device:C", value, fp, {"1": a, "2": b}, sch, pcb, rot,
      desc=kw.pop("desc", "Capacitor %s 16V X7R %s" % (value, fp.split(":")[1].split("_")[1])), **kw)


# ---------------------------------------------------------------- USB-C input
P("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C 16P",
  "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
  {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
   "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
   "A5": "CC1", "B5": "CC2",
   "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
   "A8": None, "B8": None},
  sch=(14, 28), pcb=(12, 42.4, 0),
  mpn="TYPE-C-31-M-12", mfr="Korean Hroparts (HRO)",
  desc="USB Type-C receptacle, 16 pin, USB 2.0, SMT")
R("R1", "5.1k", "CC1", "GND", (32, 20), (5.0, 33.2, 90))
R("R2", "5.1k", "CC2", "GND", (37, 20), (17.0, 33.2, 90))
P("U5", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6",
  "Package_TO_SOT_SMD:SOT-23-6",
  {"1": "USB_DM", "6": "USB_DM", "3": "USB_DP", "4": "USB_DP",
   "5": "+5V", "2": "GND"},
  ref_at=(3.2, -6.3), val_at=(3.2, -4.6), sch=(48, 22), pcb=(12, 34.4, 0),
  mpn="USBLC6-2SC6", mfr="STMicroelectronics",
  desc="USB ESD protection diode array")
P("F1", "Device:Polyfuse", "2.6A PTC", "Fuse:Fuse_1812_4532Metric",
  {"1": "VBUS", "2": "+5V"}, sch=(32, 40), pcb=(22, 38.8, 90), rot=180,
  mpn="1812L260/16", mfr="Littelfuse (or equivalent)",
  desc="Resettable fuse, 2.6 A hold, 1812")
C("C1", "22uF", "+5V", "GND", (38, 40), (22.6, 31.8, 0), fp=C0805,
  desc="Capacitor 22uF 10V X5R 0805")
P("TP1", "Connector:TestPoint", "+5V", TP, {"1": "+5V"},
  sch=(44, 40), pcb=(36, 44, 0), rot=180, desc="Test pad", bom=False)
P("TP3", "Connector:TestPoint", "GND", TP, {"1": "GND"},
  sch=(50, 38), pcb=(39, 44, 0), desc="Test pad", bom=False)

# ---------------------------------------------------------- 3.3 V regulator
P("D1", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
  {"1": "VLDO", "2": "+5V"}, ref_at=(0, -3.2, "center"), val_at=(0, 3.4, "center"),
  sch=(69, 20), pcb=(27, 33, 0),
  mpn="B5819W", mfr="generic", desc="Schottky diode 40V 1A SOD-123")
P("C2", "Device:C_Polarized", "100uF 10V", "Capacitor_SMD:CP_Elec_6.3x5.4",
  {"1": "VLDO", "2": "GND"}, sch=(74, 20), pcb=(29.5, 39.5, 0),
  desc="Aluminium electrolytic 100uF 10V, 6.3x5.4 mm SMD")
C("C3", "1uF", "VLDO", "GND", (79, 20), (31.3, 31.8, 0))
P("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3",
  "Package_TO_SOT_SMD:SOT-23-5",
  {"1": "VLDO", "3": "VLDO", "2": "GND", "5": "+3V3", "4": None},
  ref_at=(-7.62, -9.2), val_at=(-7.62, -7.4), sch=(90, 20), pcb=(36.5, 38.6, 0),
  mpn="AP2112K-3.3TRG1", mfr="Diodes Inc.",
  desc="3.3 V 600 mA low-dropout regulator")
C("C4", "10uF", "+3V3", "GND", (100, 20), (39.2, 31.8, 0), fp=C0805,
  desc="Capacitor 10uF 10V X5R 0805")
P("TP2", "Connector:TestPoint", "+3V3", TP, {"1": "+3V3"},
  sch=(105, 20), pcb=(42, 44, 0), rot=180, desc="Test pad", bom=False)

# ------------------------------------------------------------ VH head switch
P("Q1", "Transistor_FET:AO3401A", "AO3401A", SOT23,
  {"1": "VH_GATE", "2": "+5V", "3": "VH"},
  ref_at=(3.5, -4.6), val_at=(3.5, -2.9), sch=(134, 22), pcb=(17, 26, 0), rot=180,
  mpn="AO3401A", mfr="Alpha & Omega",
  desc="P-channel MOSFET 30V 4A, VH high-side switch")
R("R11", "1M", "+5V", "VH_GATE", (146, 18), (22.2, 28.3, 0))
R("R10", "150k", "VH_GATE", "Q2_D", (151, 20), (22.2, 26.6, 0))
C("C10", "100nF", "VH_GATE", "VH", (156, 20), (22.2, 24.9, 0))
P("Q2", "Transistor_FET:2N7002", "2N7002", SOT23,
  {"1": "VH_EN", "2": "GND", "3": "Q2_D"},
  ref_at=(5.2, -1.2), val_at=(5.2, 1.4), sch=(134, 40), pcb=(26, 26, 0),
  mpn="2N7002", mfr="generic", desc="N-channel MOSFET 60V, level shifter")
R("R9", "10k", "VH_EN", "GND", (122, 40), (26.4, 23.0, 0))
P("C11", "Device:C_Polarized", "1000uF",
  "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
  {"1": "VH", "2": "GND"}, sch=(146, 40), pcb=(6.25, 24, 0),
  desc="Aluminium electrolytic 1000uF 10V low-ESR, 8 mm dia, 3.5 mm pitch")
P("C12", "Device:C_Polarized", "1000uF",
  "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
  {"1": "VH", "2": "GND"}, sch=(151, 40), pcb=(6.25, 14, 0),
  desc="Aluminium electrolytic 1000uF 10V low-ESR, 8 mm dia, 3.5 mm pitch")
P("TP4", "Connector:TestPoint", "VH", TP, {"1": "VH"},
  sch=(157, 38), pcb=(45, 44, 0), desc="Test pad", bom=False)

# ----------------------------------------------------------------------- MCU
P("U1", "RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4",
  "RF_Module:ESP32-C3-WROOM-02",
  {"1": "+3V3", "9": "GND", "19": "GND", "2": "EN",
   "18": "TM_ADC",       # IO0  ADC1_CH0  head thermistor
   "17": "PS_ADC",       # IO1  ADC1_CH1  paper sensor
   "16": "HEAD_LAT",     # IO2  strapping, pulled up
   "15": "VH_SENSE",     # IO3  ADC1_CH3  head rail voltage
   "3": "HEAD_CLK",      # IO4
   "4": "VH_EN",         # IO5
   "5": "HEAD_DI",       # IO6
   "6": "HEAD_STB_A",    # IO7
   "7": "LED_DIN",       # IO8  strapping, pulled up
   "8": "BTN",           # IO9  strapping / boot button
   "10": "HEAD_STB_B",   # IO10
   "13": "USB_DM",       # IO18
   "14": "USB_DP",       # IO19
   "11": "MOT_PH_A",     # IO20
   "12": "MOT_PH_B"},    # IO21
  ref_at=(-15.24, -23.8), val_at=(2.6, -23.8), sch=(30, 86), pcb=(49.2, 28, 270),
  mpn="ESP32-C3-WROOM-02-N4", mfr="Espressif",
  desc="Wi-Fi + Bluetooth LE module, RISC-V, 4 MB flash, PCB antenna")
R("R3", "10k", "+3V3", "EN", (12, 63), (37.0, 24.6, 90))
C("C7", "1uF", "EN", "GND", (17, 63), (37.0, 21.4, 90))
C("C5", "100nF", "+3V3", "GND", (22, 63), (39.0, 27.2, 0))
C("C6", "10uF", "+3V3", "GND", (27, 63), (39.2, 29.2, 0), fp=C0805,
  desc="Capacitor 10uF 10V X5R 0805")
R("R4", "10k", "+3V3", "HEAD_LAT", (33, 63), (57.5, 32.4, 0))
R("R5", "10k", "+3V3", "LED_DIN", (39, 63), (45.5, 32.4, 0))
R("R6", "10k", "+3V3", "BTN", (45, 63), (49.0, 32.4, 0))
C("C8", "100nF", "BTN", "GND", (51, 63), (52.5, 32.4, 0))
P("TP5", "Connector:TestPoint", "EN", TP, {"1": "EN"},
  sch=(56, 62), pcb=(48, 44, 0), desc="Test pad", bom=False)
P("SW1", "Switch:SW_Push", "BTN / BOOT", "Button_Switch_THT:SW_PUSH_6mm",
  {"1": "BTN", "2": "GND"}, ref_at=(0, -4.2, "center"), val_at=(0, 3.4, "center"), sch=(53, 82), pcb=(31.5, 22.5, 0),
  mpn="TS-1187 / B3F class", mfr="generic",
  desc="Tactile switch 6x6 mm through-hole; actuator height to suit keycap")
P("D2", "LED:SK6812MINI", "SK6812MINI",
  "LED_SMD:LED_SK6812MINI_PLCC4_3.5x3.5mm_P1.75mm",
  {"4": "+3V3", "2": "GND", "3": "LED_DIN", "1": None},
  ref_at=(2.6, -6.2), val_at=(2.6, 6.4), sch=(52, 97), pcb=(36, 31.5, 0),
  mpn="SK6812MINI", mfr="Opsco / Worldsemi", desc="Addressable RGB LED 3535")
C("C9", "100nF", "+3V3", "GND", (60, 97), (41.5, 33.9, 0))

# -------------------------------------------------------------- motor driver
P("U3", "Driver_Motor:DRV8833PW", "DRV8833PW",
  "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
  {"1": "VH_EN", "16": "MOT_PH_A", "15": "MOT_PH_A_N",
   "9": "MOT_PH_B", "10": "MOT_PH_B_N",
   "2": "MOT_A1", "4": "MOT_A2", "7": "MOT_B1", "5": "MOT_B2",
   "3": "AISEN", "6": "BISEN", "11": "VCP", "12": "VH", "14": "VINT",
   "13": "GND", "8": None},
  ref_at=(-12.7, -17.6), val_at=(-12.7, -15.8), sch=(84, 84), pcb=(19, 13, 270),
  mpn="DRV8833PWR", mfr="Texas Instruments (or pin-compatible)",
  desc="Dual H-bridge motor driver, 1.5 A, TSSOP-16")
R("R17", "0.2R", "AISEN", "GND", (66, 63), (33.6, 16.6, 0), fp=R0805,
  desc="Current-sense resistor 0.2 ohm 1% 0805 (1 A limit)")
R("R18", "0.2R", "BISEN", "GND", (71, 63), (29.4, 16.6, 0), fp=R0805,
  desc="Current-sense resistor 0.2 ohm 1% 0805 (1 A limit)")
C("C21", "2.2uF", "VINT", "GND", (76, 63), (27.0, 7.4, 0))
C("C22", "10nF", "VCP", "VH", (81, 63), (31.0, 7.4, 0),
  desc="Capacitor 10nF 16V X7R (charge pump)")
C("C19", "10uF", "VH", "GND", (88, 63), (35.2, 7.4, 0), fp=C0805,
  desc="Capacitor 10uF 16V X5R 0805")
C("C20", "100nF", "VH", "GND", (93, 63), (35.0, 9.6, 0))
P("U4", "74xGxx:74LVC2G04", "74LVC2G04",
  "Package_TO_SOT_SMD:SOT-363_SC-70-6",
  {"1": "MOT_PH_A", "6": "MOT_PH_A_N", "3": "MOT_PH_B", "4": "MOT_PH_B_N",
   "5": "+3V3", "2": "GND"},
  ref_at=(-7.0, -5.0), val_at=(3.6, 6.5), sch=(80, 98), pcb=(26, 15.5, 0),
  units={1: (80, 98), 2: (80, 104), 3: (96, 101)},
  mpn="74LVC2G04GW", mfr="Nexperia (or equivalent)",
  desc="Dual inverter, generates complementary motor phase signals")
C("C23", "100nF", "+3V3", "GND", (101, 101), (36.3, 16.6, 0))

# ----------------------------------------------------------- print mechanism
HEAD_PINS = [
    ("1", "PHK", "PS_K"), ("2", "VSEN", "+3V3"), ("3", "PHE", "PS_ADC"),
    ("4", "NC", None), ("5", "NC", None),
    ("6", "VH", "VH"), ("7", "VH", "VH"),
    ("8", "DI", "HEAD_DI"), ("9", "CLK", "HEAD_CLK"),
    ("10", "GND", "GND"), ("11", "GND", "GND"),
    ("12", "STB6", "HEAD_STB_B"), ("13", "STB5", "HEAD_STB_B"),
    ("14", "STB4", "HEAD_STB_B"),
    ("15", "VDD", "+3V3"), ("16", "TM", "TM_ADC"), ("17", "TM", "GND"),
    ("18", "STB3", "HEAD_STB_A"), ("19", "STB2", "HEAD_STB_A"),
    ("20", "STB1", "HEAD_STB_A"),
    ("21", "GND", "GND"), ("22", "GND", "GND"),
    ("23", "LAT", "HEAD_LAT"), ("24", "DO", "HEAD_DO"),
    ("25", "VH", "VH"), ("26", "VH", "VH"),
    ("27", "MT_A", "MOT_A1"), ("28", "MT_/A", "MOT_A2"),
    ("29", "MT_B", "MOT_B2"), ("30", "MT_/B", "MOT_B1"),
    ("MP", "SHELL", "GND"),
]
P("J2", "minai:PrintMech_FTP-628MCL101", "FTP-628MCL101 / PT486F",
  "Connector_FFC-FPC:Molex_200528-0300_1x30-1MP_P1.00mm_Horizontal",
  {n: net for n, _, net in HEAD_PINS},
  sch=(148, 80), pcb=(31, 5.0, 180), labels_only=True,
  mpn="200528-0300 (Fujitsu specifies Molex 52610-3071)", mfr="Molex",
  desc="FFC/FPC connector 30 pos 1.0 mm pitch, right angle ZIF")
R("R14", "220R", "PS_K", "GND", (108, 64), (51.0, 4.2, 0),
  desc="Resistor 220R (paper sensor LED current)")
R("R15", "47k", "PS_ADC", "GND", (113, 64), (55.0, 4.2, 0),
  desc="Resistor 47k (paper sensor load)")
R("R16", "30k 1%", "+3V3", "TM_ADC", (118, 64), (51.0, 6.2, 0),
  desc="Resistor 30k 1% (thermistor divider)")
C("C18", "100nF", "TM_ADC", "GND", (123, 64), (55.0, 6.2, 0))
P("TP6", "Connector:TestPoint", "HEAD_DO", TP, {"1": "HEAD_DO"},
  sch=(129, 63), pcb=(51.5, 44, 0), desc="Test pad", bom=False)
C("C13", "10uF", "VH", "GND", (108, 81), (21.5, 7.4, 0), fp=C0805,
  desc="Capacitor 10uF 16V X5R 0805")
C("C14", "100nF", "VH", "GND", (113, 81), (17.5, 7.4, 0))
C("C17", "100nF", "+3V3", "GND", (118, 81), (41.0, 7.4, 0))
R("R7", "10k", "HEAD_STB_A", "GND", (123, 81), (41.0, 9.4, 0))
R("R8", "10k", "HEAD_STB_B", "GND", (129, 81), (41.0, 11.4, 0))
R("R12", "100k 1%", "VH", "VH_SENSE", (108, 98), (37.0, 18.4, 90))
R("R13", "68k 1%", "VH_SENSE", "GND", (113, 98), (39.0, 18.4, 90))
C("C15", "100nF", "VH_SENSE", "GND", (118, 98), (39.0, 21.6, 90))

# ---------------------------------------------------------------- mechanical
for i, (x, y) in enumerate([(3.0, 3.0), (59.0, 3.0), (3.0, 46.0), (59.0, 46.2)]):
    P("H%d" % (i + 1), "Mechanical:MountingHole", "M2", HOLE, {},
      sch=(8 + 5 * i, 47), pcb=(x, y, 0), desc="Mounting hole M2", bom=False)

# Nets that get wide tracks on the board.
POWER_NETS = ["VBUS", "+5V", "VH", "GND"]
LOGIC_POWER_NETS = ["VLDO", "+3V3"]      # under 0.5 A, 0.3 mm tracks
MOTOR_NETS = ["MOT_A1", "MOT_A2", "MOT_B1", "MOT_B2", "AISEN", "BISEN"]

# Power-flag markers so the electrical rules check knows these nets are driven.
PWR_FLAGS = [("GND", (56, 47)), ("VLDO", (84, 30)), ("VH", (160, 30)),
             ("VINT", (98, 80)), ("+5V", (56, 38))]

SCH_TITLES = [
    ((6, 8), "1  USB-C power input, 5 V"),
    ((62, 8), "2  3.3 V logic supply"),
    ((116, 8), "3  VH head-power switch with soft start"),
    ((6, 54), "4  MCU: ESP32-C3 Wi-Fi / BLE module, button, status LED"),
    ((64, 54), "5  Paper-feed stepper driver"),
    ((104, 54), "6  Print mechanism connector, sensors, VH sense"),
]
SCH_NOTES = [
    ((6, 108.5), "REFERENCE DESIGN, NOT YET BUILT OR TESTED. J2 pinout follows the Fujitsu FTP-628MCL101 datasheet; "
               "confirm pinout, strobe polarity and FPC contact side against the mechanism actually purchased."),
    ((6, 110.5), "Strobes are assumed active-high (R7, R8 pull down). If the head is active-low, fit R7/R8 to +3V3 instead."),
    ((116, 48), "VH_EN high -> Q2 on -> Q1 on. C10/R10 slow the turn-on to ~20 ms to limit inrush into C11/C12."),
    ((6, 112.5), "U4 makes IN2 = NOT IN1, so two MCU pins drive the motor in 2-phase full step. U3 sleeps when VH_EN is low."),
]

# ------------------------------------------------------------ board placement
# (x mm, y mm, rotation deg) from the top-left board corner. This table is
# authoritative; it overrides the provisional positions given above.
PCB_POS = {
    "J1": (12, 45.4, 0), "R1": (6.5, 38.5, 90), "R2": (17.5, 38.5, 90), "U5": (12, 37.4, 0),
    "F1": (22, 41.5, 90), "C1": (22, 35.5, 0), "D1": (27, 33, 0), "C2": (29.5, 39.5, 0),
    "C3": (31.5, 33, 0), "U2": (36.5, 38.6, 0), "C4": (40, 39.5, 90),
    "Q1": (17, 27.5, 0), "R11": (21.5, 25.6, 0), "R10": (21.5, 27.5, 0), "C10": (21.5, 29.4, 0),
    "Q2": (26, 28.2, 0), "R9": (26, 25, 0), "C11": (6.25, 24, 0), "C12": (6.25, 14, 0),
    "U1": (49.2, 28, 270), "R3": (45.8, 15.0, 0), "C7": (42.6, 15.0, 0), "C5": (52.2, 15.0, 0),
    "C6": (49.0, 15.0, 0), "R4": (47.5, 40, 0), "R5": (39.4, 17, 0), "R6": (39.4, 19, 0),
    "C8": (39.6, 21, 0), "SW1": (29.8, 23.5, 0), "D2": (36, 31.5, 0), "C9": (36, 34.5, 0),
    "U3": (19, 15.5, 270), "R17": (25, 11.4, 0), "R18": (25, 13.4, 0), "C21": (20.5, 22.2, 0),
    "C22": (17.3, 22.2, 0), "C19": (13.8, 20.2, 90), "C20": (23.7, 22.2, 0),
    "U4": (25.5, 17.6, 0), "C23": (28.6, 17.6, 90),
    "J2": (31, 5.0, 180), "R14": (46, 9, 0), "R15": (46, 11, 0), "R16": (30.5, 9, 0),
    "C18": (30.5, 11, 0), "C13": (40.5, 9, 0), "C14": (40.5, 11, 0), "C17": (34, 9, 0),
    "R7": (27.3, 8.8, 0), "R8": (34, 11, 0), "R12": (51, 39.8, 0), "R13": (54, 39.8, 0),
    "C15": (54, 41.6, 0),
    "TP1": (36, 46.5, 0), "TP3": (39, 46.5, 0), "TP2": (42, 46.5, 0), "TP4": (45, 46.5, 0),
    "TP5": (48, 46.5, 0), "TP6": (51, 46.5, 0),
}
for _p in PARTS:
    if _p["ref"] in PCB_POS:
        _p["pcb"] = PCB_POS[_p["ref"]]
    elif not _p["ref"].startswith("H"):
        raise SystemExit("no board position for " + _p["ref"])
