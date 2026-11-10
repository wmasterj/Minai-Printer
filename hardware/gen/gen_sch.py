"""Generate minai-printer.kicad_sch from design.py (run inside the KiCad container)."""
import copy
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from sx import parse, dump, q, uq
import design as D

SYMDIR = "/usr/share/kicad/symbols/"
OUT = sys.argv[1]
U = 2.54
NS = uuid.UUID("6d696e61-692d-7072-696e-746572000000")
_n = [0]


def uid(tag=""):
    _n[0] += 1
    return str(uuid.uuid5(NS, "%s-%d" % (tag, _n[0])))


ROOT = str(uuid.uuid5(NS, "root"))
POWER_SYMS = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V"}
_libcache = {}


def fnum(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------ library access
def custom_head_symbol():
    pins = D.HEAD_PINS
    n = len(pins)
    top = 14 * U
    body = ["symbol", q("PrintMech_FTP-628MCL101_1_1"),
            ["rectangle", ["start", fnum(-4 * U), fnum(top + 1.5 * U)],
             ["end", fnum(5 * U), fnum(top - (n - 1) * U - 1.5 * U)],
             ["stroke", ["width", "0.254"], ["type", "default"]],
             ["fill", ["type", "background"]]]]
    for i, (num, name, _) in enumerate(pins):
        body.append(["pin", "passive", "line",
                     ["at", fnum(-5 * U), fnum(top - i * U), "0"], ["length", "2.54"],
                     ["name", q(name), ["effects", ["font", ["size", "1.27", "1.27"]]]],
                     ["number", q(num), ["effects", ["font", ["size", "1.27", "1.27"]]]]])

    def prop(k, v, y, hide=False):
        e = ["effects", ["font", ["size", "1.27", "1.27"]]]
        if hide:
            e.append(["hide", "yes"])
        return ["property", q(k), q(v), ["at", "0", fnum(y), "0"], e]

    return ["symbol", q("PrintMech_FTP-628MCL101"),
            ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            prop("Reference", "J", top + 3 * U), prop("Value", "PrintMech_FTP-628MCL101", top + 2 * U),
            prop("Footprint", "", 0, True), prop("Datasheet", "", 0, True),
            prop("Description", "58 mm thermal print mechanism, 30-pin FPC", 0, True),
            body]


def load_symbol(lib_id):
    """Return a flattened symbol definition named with its full lib_id."""
    if lib_id in _libcache:
        return _libcache[lib_id]
    lib, name = lib_id.split(":")
    if lib == "minai":
        sym = custom_head_symbol()
    else:
        if lib not in _libcache:
            _libcache[lib] = parse(open(SYMDIR + lib + ".kicad_sym").read())
        tree = _libcache[lib]
        byname = {uq(s[1]): s for s in tree[1:] if isinstance(s, list) and s[0] == "symbol"}
        sym = copy.deepcopy(byname[name])
        ext = [c for c in sym if isinstance(c, list) and c[0] == "extends"]
        if ext:
            pname = uq(ext[0][1])
            parent = copy.deepcopy(byname[pname])
            cprops = {uq(c[1]): c for c in sym if isinstance(c, list) and c[0] == "property"}
            new = []
            for c in parent:
                if isinstance(c, list) and c[0] == "property" and uq(c[1]) in cprops:
                    new.append(cprops.pop(uq(c[1])))
                elif isinstance(c, list) and c[0] == "symbol":
                    c[1] = q(name + uq(c[1])[len(pname):])
                    new.append(c)
                else:
                    new.append(c)
            new[1] = q(name)
            sym = new
    sym[1] = q(lib_id)
    _libcache[lib_id] = sym
    return sym


def sym_pins(sym):
    """[(unit, number, name, x, y, angle, hidden)] in library coordinates."""
    base = uq(sym[1]).split(":")[1]
    out = []
    for c in sym:
        if isinstance(c, list) and c[0] == "symbol":
            unit = int(uq(c[1])[len(base) + 1:].split("_")[0])
            for p in c:
                if isinstance(p, list) and p[0] == "pin":
                    d = {k[0]: k for k in p if isinstance(k, list)}
                    hidden = "hide" in d and d["hide"][1:] != ["no"] or "hide" in p
                    out.append((unit, uq(d["number"][1]), uq(d["name"][1]),
                                float(d["at"][1]), float(d["at"][2]), int(d["at"][3]), hidden))
    return out


def sym_prop(sym, key):
    for c in sym:
        if isinstance(c, list) and c[0] == "property" and uq(c[1]) == key:
            return c
    return None


def xf(x, y, rot):
    a = math.radians(rot)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


# ------------------------------------------------------------------- output
items = []
used_libs = {}
pwr_count = [0]
EFF = ["effects", ["font", ["size", "1.27", "1.27"]]]


def effects(justify=None, hide=False, size=1.27):
    e = ["effects", ["font", ["size", fnum(size), fnum(size)]]]
    if justify and justify != "center":
        e.append(["justify"] + justify.split())
    if hide:
        e.append(["hide", "yes"])
    return e


def place(lib_id, ref, value, x, y, rot=0, unit=1, fp="", fields=None, in_bom=True,
          ref_at=None, val_at=None, hide_ref=False):
    sym = load_symbol(lib_id)
    used_libs[lib_id] = sym
    s = ["symbol", ["lib_id", q(lib_id)], ["at", fnum(x), fnum(y), str(rot)], ["unit", str(unit)],
         ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"], ["on_board", "yes"],
         ["dnp", "no"], ["uuid", uid(ref)]]

    def pos(key, override):
        if override:
            return override
        p = sym_prop(sym, key)
        px, py = float(p[3][1]), float(p[3][2])
        rx, ry = xf(px, py, rot)
        return (x + rx, y - ry, int(p[3][3]) if rot == 0 else 0)

    rp, vp = pos("Reference", ref_at), pos("Value", val_at)

    def fix(p):
        # KiCad rotates field text with the symbol; compensate so it reads normally.
        p = list(p) + [None] * (4 - len(p))
        if rot in (90, 270):
            p[2] = 90
        if rot == 180 and p[3] in ("left", "right"):
            p[3] = "right" if p[3] == "left" else "left"
        return p

    rp, vp = fix(rp), fix(vp)
    s.append(["property", q("Reference"), q(ref), ["at", fnum(rp[0]), fnum(rp[1]), str(rp[2])],
              effects(rp[3] if len(rp) > 3 else None, hide_ref)])
    s.append(["property", q("Value"), q(value), ["at", fnum(vp[0]), fnum(vp[1]), str(vp[2])],
              effects(vp[3] if len(vp) > 3 else None)])
    s.append(["property", q("Footprint"), q(fp), ["at", fnum(x), fnum(y), "0"], effects(hide=True)])
    s.append(["property", q("Datasheet"), q(""), ["at", fnum(x), fnum(y), "0"], effects(hide=True)])
    for k, v in (fields or {}).items():
        if v:
            s.append(["property", q(k), q(v), ["at", fnum(x), fnum(y), "0"], effects(hide=True)])
    for (_, num, *_r) in sym_pins(sym):
        s.append(["pin", q(num), ["uuid", uid(ref + num)]])
    s.append(["instances", ["project", q("minai-printer"),
                            ["path", q("/" + ROOT), ["reference", q(ref)], ["unit", str(unit)]]]])
    items.append(s)
    return sym


def wire(x1, y1, x2, y2):
    items.append(["wire", ["pts", ["xy", fnum(x1), fnum(y1)], ["xy", fnum(x2), fnum(y2)]],
                  ["stroke", ["width", "0"], ["type", "default"]], ["uuid", uid("w")]])


def glabel(net, x, y, direction):
    rot = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[direction]
    just = "left" if rot in (0, 90) else "right"
    items.append(["global_label", q(net), ["shape", "passive"], ["at", fnum(x), fnum(y), str(rot)],
                  ["fields_autoplaced", "yes"], effects(just), ["uuid", uid("l" + net)],
                  ["property", q("Intersheetrefs"), q("${INTERSHEET_REFS}"),
                   ["at", fnum(x), fnum(y), "0"], effects(hide=True)]])


def power(net, x, y, direction=None):
    """Place a power symbol upright at (x, y); the pin is at the symbol origin."""
    pwr_count[0] += 1
    lib_id = POWER_SYMS[net]
    down = net == "GND"
    place(lib_id, "#PWR%03d" % pwr_count[0], net, x, y, 0, in_bom=False, hide_ref=True,
          ref_at=(x, y + (6.35 if down else -6.35), 0),
          val_at=(x, y + (4.6 if down else -4.0), 0))


def connect(net, x, y, d, labels_only=False):
    """Attach net to a pin endpoint at (x, y); d is the outward direction."""
    if net in POWER_SYMS and not labels_only:
        natural = (0, 1) if net == "GND" else (0, -1)
        if d == natural:
            power(net, x, y)
        elif d[1] == 0:                      # side pin: stub out, then symbol
            ex = x + d[0] * U
            wire(x, y, ex, y)
            power(net, ex, y)
        else:                                # pin faces the wrong way
            ex = x + U
            ey = y + d[1] * U
            wire(x, y, x, ey)
            wire(x, ey, ex, ey)
            power(net, ex, ey)
    else:
        glabel(net, x, y, d)


def noconnect(x, y):
    items.append(["no_connect", ["at", fnum(x), fnum(y)], ["uuid", uid("nc")]])


def text(s, x, y, size=1.27, bold=False):
    font = ["font", ["size", fnum(size), fnum(size)]]
    if bold:
        font.append(["bold", "yes"])
    items.append(["text", q(s), ["exclude_from_sim", "no"], ["at", fnum(x), fnum(y), "0"],
                  ["effects", font, ["justify", "left", "bottom"]], ["uuid", uid("t")]])


OUTWARD = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # sheet coords (y down)

for part in D.PARTS:
    lib_id = part["lib"]
    sym = load_symbol(lib_id)
    pins = sym_pins(sym)
    units = part.get("units") or {1: part["sch"]}
    two_pin = lib_id in ("Device:R", "Device:C", "Device:C_Polarized", "Device:Polyfuse")
    fields = {"MPN": part["mpn"], "Manufacturer": part["mfr"], "Description": part["desc"]}
    for unit, (ux, uy) in units.items():
        x, y, rot = ux * U, uy * U, part["rot"]
        kw = {}
        for k in ("ref_at", "val_at"):
            if k in part:
                o = part[k]
                kw[k] = (x + o[0], y + o[1], 0, o[2] if len(o) > 2 else "left")
        if kw:
            pass
        elif two_pin or lib_id == "Device:D_Schottky":
            kw = dict(ref_at=(x + (2.9 if "fuse" in lib_id else 1.9), y - 1.1, 0, "left"),
                      val_at=(x + (2.9 if "fuse" in lib_id else 1.9), y + 1.3, 0, "left"))
        elif lib_id == "Connector:TestPoint":
            kw = dict(ref_at=(x + 2.2, y - 2.0 if rot == 0 else y + 2.6, 0, "left"),
                      val_at=(x, y, 0))
        place(lib_id, part["ref"], part["value"], x, y, rot, unit, part["fp"], fields,
              in_bom=part.get("bom", True), **kw)
        if lib_id == "Connector:TestPoint" or (part.get("units") and unit != max(units)):
            items[-1][10][-1].append(["hide", "yes"])     # hide the value text
        seen = set()
        for (pu, num, name, px, py, pa, hidden) in pins:
            if pu not in (0, unit):
                continue
            if pu == 0 and unit != min(units):
                continue
            rx, ry = xf(px, py, rot)
            ex, ey = round(x + rx, 4), round(y - ry, 4)
            ang = (pa + rot) % 360
            if num not in part["nets"]:
                raise SystemExit("%s pin %s has no net entry" % (part["ref"], num))
            net = part["nets"][num]
            key = (ex, ey, net)
            if key in seen:
                continue
            seen.add(key)
            if hidden and any(k[:2] == (ex, ey) for k in seen if k != key):
                continue
            if net is None:
                noconnect(ex, ey)
            else:
                connect(net, ex, ey, OUTWARD[ang], part.get("labels_only", False))
    missing = set(part["nets"]) - {p[1] for p in pins}
    if missing:
        raise SystemExit("%s: nets given for unknown pins %s" % (part["ref"], missing))

for i, (net, (fx, fy)) in enumerate(D.PWR_FLAGS):
    x, y = fx * U, fy * U
    place("power:PWR_FLAG", "#FLG%02d" % (i + 1), "PWR_FLAG", x, y, 0, in_bom=False, hide_ref=True,
          ref_at=(x, y - 5.0, 0), val_at=(x, y - 3.3, 0))
    if net == "GND":
        power(net, x, y)
    else:
        glabel(net, x, y, (0, 1))

for (tx, ty), s in D.SCH_TITLES:
    text(s, tx * U, ty * U, 2.2, True)
for (tx, ty), s in D.SCH_NOTES:
    text(s, tx * U, ty * U, 1.4)

sheet = ["kicad_sch", ["version", "20250114"], ["generator", q("minai_gen")],
         ["generator_version", q("9.0")], ["uuid", q(ROOT)], ["paper", q("A3")],
         ["title_block", ["title", q("Minai Printer - main board reference design")],
          ["date", q("2026-11-10")], ["rev", q("0.1")], ["company", q("Minai Printer")],
          ["comment", "1", q("Generated from hardware/gen/design.py - edit there, not here")],
          ["comment", "2", q("Reference design. Not built or tested.")]],
         ["lib_symbols"] + list(used_libs.values())]
sheet += items
sheet += [["sheet_instances", ["path", q("/"), ["page", q("1")]]], ["embedded_fonts", "no"]]


def fix_uuid(node):
    for c in node:
        if isinstance(c, list):
            if c[0] == "uuid" and not c[1].startswith('"'):
                c[1] = q(c[1])
            fix_uuid(c)


fix_uuid(sheet)
open(OUT, "w").write(dump(sheet) + "\n")
print("wrote", OUT, "symbols:", sum(1 for i in items if i[0] == "symbol"))
