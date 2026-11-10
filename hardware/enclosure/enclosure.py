"""Minai Printer enclosure, rev 0.1 (CadQuery).

    pip install cadquery
    python3 hardware/enclosure/enclosure.py

Writes STEP and STL files for each printed part to hardware/enclosure/out/,
plus meshes.json for the 3D viewer.

Axes: X = width, Y = depth (front of the printer at Y = 0), Z = up. All mm.

The print mechanism, paper roll and circuit board are stand-in blocks. The
mechanism block (70 x 31 x 16) is an assumed envelope, not taken from a
datasheet: the mounting posts and paper slot must be redrawn around the
real mechanism.
"""
import base64
import json
import os
import struct

import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------- parameters
T = 2.4                     # wall thickness
WI = 72.0                   # inner width
ROLL_BAY = 46.0             # inner depth of the paper bay (40 mm roll + clearance)
ROLL_D, ROLL_W = 40.0, 57.5
MECH = (70.0, 31.0, 16.0)   # ASSUMED mechanism envelope W x D x H
MECH_OVERHANG = 9.0         # mechanism sits this far forward of the board edge
PCB = (62.0, 49.0, 1.6)     # reference main board
STANDOFF = 4.0              # board underside above the floor
H = 50.0                    # outer height
SPLIT = 34.0                # base / top-cover split line
R_OUT = 6.0                 # outer corner radius
SLOT = 3.0                  # paper exit slot

W = WI + 2 * T
Y_BAY0 = T
Y_DIV = Y_BAY0 + ROLL_BAY                  # front face of the divider wall
Y_PCB0 = Y_DIV + MECH_OVERHANG             # board front edge
Y_PCB1 = Y_PCB0 + PCB[1]
D = Y_PCB1 + 0.5 + T                       # outer depth
X_PCB0 = (W - PCB[0]) / 2
Z_PCB = T + STANDOFF                       # board underside
Z_PCB_TOP = Z_PCB + PCB[2]
Z_MECH = 24.0                              # mechanism underside (clears 12.5 mm capacitors)
Y_SLOT0 = Y_DIV + 0.6                      # paper slot, front edge (= lid rear edge)
Y_SLOT1 = Y_SLOT0 + SLOT

# positions taken from the board layout (board coords -> enclosure coords)
def b2e(x, y):
    return (X_PCB0 + x, Y_PCB0 + y)

HOLES = [b2e(3, 3), b2e(59, 3), b2e(3, 46), b2e(59, 46.2)]
USB_X, _ = b2e(12, 45.4)
BTN = b2e(33.05, 25.75)
LED = b2e(36, 31.5)
SCREWS = [(T + 2.5, D - T - 3.0), (W - T - 2.5, D - T - 3.0)]


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(x, y, z0, z1, r):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def cyl_x(x0, x1, y, z, r):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def rounded(z0, z1, inset, r):
    b = box(inset, inset, z0, W - inset, D - inset, z1)
    return b.edges("|Z").fillet(r)


# -------------------------------------------------------------------- base
def make_base():
    s = rounded(0, SPLIT, 0, R_OUT).cut(rounded(T, SPLIT + 1, T, R_OUT - T))
    # divider between paper bay and electronics, kept below the mechanism
    s = s.union(box(T, Y_DIV, T, W - T, Y_DIV + 1.6, Z_MECH - 1))
    # paper roll side guides and two low ribs that centre the roll
    gx = (W - (ROLL_W + 2.5)) / 2
    for x in (gx - 1.6, W - gx):
        s = s.union(box(x, Y_BAY0, T, x + 1.6, Y_DIV, SPLIT - 1))
    yc = Y_BAY0 + ROLL_BAY / 2
    for y in (yc - 13, yc + 13):
        s = s.union(box(gx, y - 1, T, W - gx, y + 1, T + 3.5))
    # board standoffs with pilot holes for M2 self-tapping screws
    for (x, y) in HOLES:
        s = s.union(cyl_z(x, y, T, Z_PCB, 2.6)).cut(cyl_z(x, y, T + 0.8, Z_PCB + 1, 0.85))
    # mechanism posts (placeholder geometry)
    for x0 in (T, W - T - 3.0):
        for y0 in (Y_DIV + 2.6, Y_DIV + 21.6):
            s = s.union(box(x0, y0, T, x0 + 3.0, y0 + 7.0, Z_MECH))
    # screw bosses for the rear cover, screws enter from below
    for (x, y) in SCREWS:
        s = s.union(cyl_z(x, y, T, SPLIT, 2.4))
        s = s.cut(cyl_z(x, y, -1, SPLIT + 1, 1.25)).cut(cyl_z(x, y, -1, 1.6, 2.4))
    # USB-C opening in the rear wall
    zc = Z_PCB_TOP + 1.65
    usb = box(USB_X - 4.9, D - T - 1, zc - 2.0, USB_X + 4.9, D + 1, zc + 2.0).edges("|Y").fillet(1.6)
    s = s.cut(usb)
    # hinge knuckles on the front wall
    for x0 in (10.0, W - 22.0):
        s = s.union(cyl_x(x0, x0 + 12.0, 1.6, SPLIT, 2.2))
    return s


# ---------------------------------------------------------------- top shell
def top_shell():
    outer = rounded(SPLIT, H, 0, R_OUT).faces(">Z").edges().fillet(2.0)
    inner = rounded(SPLIT - 1, H - T, T, R_OUT - T)
    return outer.cut(inner)


def make_lid():
    s = top_shell().intersect(box(-1, -1, SPLIT - 1, W + 1, Y_SLOT0, H + 1))
    # clear the base hinge knuckles, add the lid's own centre knuckle
    for x0 in (10.0, W - 22.0):
        s = s.cut(cyl_x(x0 - 0.4, x0 + 12.4, 1.6, SPLIT, 2.7))
    s = s.union(cyl_x(24.0, W - 24.0, 1.6, SPLIT, 2.2))
    # ears that carry the platen roller at the rear edge
    px = (W - 60.0) / 2
    for x0 in (px - 3.0, W - px):
        s = s.union(box(x0, Y_SLOT0 - 9.0, SPLIT + 1.0, x0 + 3.0, Y_SLOT0, H - T))
    # finger grip at the rear of each side
    for x0 in (-1, W - 1.2):
        s = s.cut(box(x0, Y_SLOT0 - 22, SPLIT, x0 + 2.2, Y_SLOT0 - 6, SPLIT + 5))
    return s


def make_platen():
    px = (W - 60.0) / 2
    return cyl_x(px, W - px, Y_SLOT0 - 4.2, SPLIT + 6.0, 4.0)


def make_rear_cover():
    s = top_shell().intersect(box(-1, Y_SLOT1, SPLIT - 1, W + 1, D + 1, H + 1))
    # front skirt above the mechanism
    s = s.union(box(T, Y_SLOT1, Z_MECH + MECH[2] + 1.5, W - T, Y_SLOT1 + 1.6, H - T))
    # button opening and a guide collar under it
    bx, by = BTN
    s = s.union(cyl_z(bx, by, H - T - 4.0, H - T, 8.6))
    s = s.cut(cyl_z(bx, by, H - T - 5.0, H + 1, 6.2))
    # screw bosses
    for (x, y) in SCREWS:
        s = s.union(cyl_z(x, y, SPLIT, H - T, 2.4)).cut(cyl_z(x, y, SPLIT - 1, H - T - 1.5, 0.95))
    # serrated tear bar along the paper slot
    n = 24
    pitch = (ROLL_W + 2.5) / n
    x0 = (W - (ROLL_W + 2.5)) / 2
    pts = [(x0, H - 0.5)]
    for i in range(n):
        pts += [(x0 + (i + 0.5) * pitch, H + 1.8), (x0 + (i + 1) * pitch, H - 0.5)]
    teeth = cq.Workplane("XZ").polyline(pts).close().extrude(-1.0).translate((0, Y_SLOT1, 0))
    return s.union(teeth)


def make_button():
    bx, by = BTN
    s = cyl_z(bx, by, H - T - 1.0, H + 1.2, 5.9).faces(">Z").edges().fillet(1.0)
    s = s.union(cyl_z(bx, by, H - T - 6.0, H - T - 4.4, 9.5))      # flange, also catches LED light
    s = s.union(cyl_z(bx, by, Z_PCB_TOP + 5.3, H - T - 1.0, 2.2))  # stem down to the switch
    return s


# ------------------------------------------------------ stand-in components
def make_pcb():
    x0, y0 = X_PCB0, Y_PCB0
    s = box(x0, y0, Z_PCB, x0 + PCB[0], y0 + PCB[1], Z_PCB_TOP)
    for (x, y) in HOLES:
        s = s.cut(cyl_z(x, y, Z_PCB - 1, Z_PCB_TOP + 1, 1.1))
    return s


def make_pcb_parts():
    z = Z_PCB_TOP
    x0, y0 = X_PCB0, Y_PCB0
    s = box(x0 + 42.2, y0 + 19, z, x0 + 62.0, y0 + 37, z + 3.2)              # Wi-Fi module
    for cy in (14, 24):
        s = s.union(cyl_z(x0 + 8, y0 + cy, z, z + 12.5, 4.0))                # 1000 uF capacitors
    s = s.union(box(USB_X - 4.5, Y_PCB1 - 7.0, z, USB_X + 4.5, Y_PCB1 + 0.5, z + 3.3))   # USB-C
    s = s.union(box(x0 + 12.5, y0 + 0.3, z, x0 + 49.5, y0 + 6.5, z + 2.6))   # FPC connector
    s = s.union(box(BTN[0] - 3, BTN[1] - 3, z, BTN[0] + 3, BTN[1] + 3, z + 3.6))
    s = s.union(cyl_z(BTN[0], BTN[1], z + 3.6, z + 5.0, 1.7))                # switch
    s = s.union(box(LED[0] - 1.75, LED[1] - 1.75, z, LED[0] + 1.75, LED[1] + 1.75, z + 1.0))
    s = s.union(box(x0 + 29.2, y0 + 37.4, z, x0 + 36.2, y0 + 42.0, z + 5.6))  # 100 uF capacitor
    s = s.union(box(x0 + 16.8, y0 + 12.3, z, x0 + 21.2, y0 + 18.7, z + 1.1))  # motor driver
    return s


def make_mech():
    x0 = (W - MECH[0]) / 2
    s = box(x0, Y_DIV, Z_MECH, x0 + MECH[0], Y_DIV + MECH[1], Z_MECH + MECH[2])
    # relief where the platen roller closes against the head
    s = s.cut(cyl_x(x0 + 4, x0 + MECH[0] - 4, Y_SLOT0 - 4.2, SPLIT + 6.0, 4.6))
    s = s.union(cyl_x(x0 + MECH[0] - 14, x0 + MECH[0] - 2, Y_DIV + 22, Z_MECH + 6, 5.5))  # motor
    return s


def make_roll():
    x0 = (W - ROLL_W) / 2
    yc, zc = Y_BAY0 + ROLL_BAY / 2, T + 3.5 + ROLL_D / 2 - 1.6
    s = cyl_x(x0, x0 + ROLL_W, yc, zc, ROLL_D / 2).cut(cyl_x(x0 - 1, x0 + ROLL_W + 1, yc, zc, 6.5))
    return s


def make_paper():
    x0 = (W - ROLL_W) / 2
    return box(x0, Y_SLOT0 + 1.3, SPLIT + 4.0, x0 + ROLL_W, Y_SLOT0 + 1.5, H + 16.0)


PARTS = [
    # name, builder, kind, colour, printed?
    ("base", make_base, "shell", "#e9e6df", True),
    ("lid", make_lid, "lid", "#e9e6df", True),
    ("rear-cover", make_rear_cover, "cover", "#e9e6df", True),
    ("button", make_button, "button", "#ff7a3d", True),
    ("platen-roller", make_platen, "lidpart", "#2b2b2e", False),
    ("main-board", make_pcb, "inside", "#1f6b46", False),
    ("board-parts", make_pcb_parts, "inside", "#3a3d42", False),
    ("print-mechanism", make_mech, "inside", "#6c7078", False),
    ("paper-roll", make_roll, "inside", "#fbfbf7", False),
    ("paper", make_paper, "inside", "#fbfbf7", False),
]


def b64(fmt, data):
    return base64.b64encode(struct.pack("<%d%s" % (len(data), fmt), *data)).decode()


def main():
    meshes = []
    asm = cq.Assembly(name="minai-printer")
    for name, fn, kind, colour, printed in PARTS:
        solid = fn()
        shape = solid.val()
        bb = shape.BoundingBox()
        vol = shape.Volume()
        print("%-16s %6.1f x %6.1f x %5.1f mm   %7.1f cm3" %
              (name, bb.xlen, bb.ylen, bb.zlen, vol / 1000))
        if printed:
            cq.exporters.export(solid, os.path.join(OUT, name + ".step"))
            cq.exporters.export(solid, os.path.join(OUT, name + ".stl"), tolerance=0.05,
                                angularTolerance=0.2)
        asm.add(solid, name=name, color=cq.Color(*[int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        verts, tris = shape.tessellate(0.08, 0.25)
        pos = [c for v in verts for c in (v.x, v.y, v.z)]
        idx = [i for t in tris for i in t]
        meshes.append(dict(name=name, kind=kind, color=colour, printed=printed,
                           size=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
                           volume=round(vol / 1000, 1),
                           pos=b64("f", pos), idx=b64("I", idx)))
    asm.save(os.path.join(OUT, "minai-printer-assembly.step"))
    meta = dict(outer=[round(W, 1), round(D, 1), round(H, 1)], split=SPLIT,
                hinge=[1.6, SPLIT], slot=[round(Y_SLOT0, 1), round(Y_SLOT1, 1)], parts=meshes)
    json.dump(meta, open(os.path.join(OUT, "meshes.json"), "w"))
    print("outer size %.1f x %.1f x %.1f mm" % (W, D, H))


if __name__ == "__main__":
    main()
