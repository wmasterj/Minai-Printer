"""Build minai-printer.kicad_pcb from design.py (run inside the KiCad container).

  gen_pcb.py place  <board.kicad_pcb> <out.dsn>   place parts, assign nets, export for autorouter
  gen_pcb.py finish <board.kicad_pcb> <in.ses>    import routes, pour ground, save
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import design as D

FPDIR = "/usr/share/kicad/footprints/"
NETLIST = "/scratch/sch.net.xml"
OX, OY = 100.0, 100.0          # board origin on the KiCad sheet
mm = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def place(path, dsn):
    board = pcbnew.NewBoard(path)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_MinClearance = mm(0.15)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_CopperEdgeClearance = mm(0.3)
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass()
    dflt.SetClearance(mm(0.16))
    dflt.SetTrackWidth(mm(0.25))
    dflt.SetViaDiameter(mm(0.6))
    dflt.SetViaDrill(mm(0.3))
    pw = pcbnew.NETCLASS("Power")
    pw.SetClearance(mm(0.16))
    pw.SetTrackWidth(mm(0.5))
    pw.SetViaDiameter(mm(0.8))
    pw.SetViaDrill(mm(0.4))
    ns.SetNetclass("Power", pw)
    for n in D.POWER_NETS:
        ns.SetNetclassPatternAssignment(n, "Power")
    lp = pcbnew.NETCLASS("LogicPower")
    lp.SetClearance(mm(0.16))
    lp.SetTrackWidth(mm(0.3))
    lp.SetViaDiameter(mm(0.6))
    lp.SetViaDrill(mm(0.3))
    ns.SetNetclass("LogicPower", lp)
    for n in D.LOGIC_POWER_NETS:
        ns.SetNetclassPatternAssignment(n, "LogicPower")
    mt = pcbnew.NETCLASS("Motor")
    mt.SetClearance(mm(0.16))
    mt.SetTrackWidth(mm(0.35))
    mt.SetViaDiameter(mm(0.7))
    mt.SetViaDrill(mm(0.3))
    ns.SetNetclass("Motor", mt)
    for n in D.MOTOR_NETS:
        ns.SetNetclassPatternAssignment(n, "Motor")

    # outline
    r = pcbnew.PCB_SHAPE(board)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(pt(0, 0))
    r.SetEnd(pt(D.BOARD_W, D.BOARD_H))
    r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(mm(0.1))
    board.Add(r)

    nets = {}

    def net(name):
        if name not in nets:
            nets[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(nets[name])
        return nets[name]

    for p in D.PARTS:
        lib, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(FPDIR + lib + ".pretty", name)
        if fp is None:
            raise SystemExit("footprint not found: " + p["fp"])
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        x, y, rot = p["pcb"]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        padnums = set()
        for pad in fp.Pads():
            num = pad.GetNumber()
            padnums.add(num)
            if num in p["nets"] and p["nets"][num]:
                pad.SetNet(net(p["nets"][num]))
        missing = [k for k, v in p["nets"].items() if v and k not in padnums]
        if missing:
            raise SystemExit("%s: footprint %s lacks pads %s" % (p["ref"], name, missing))
        extra = [n for n in padnums if n and n not in p["nets"]]
        if extra:
            raise SystemExit("%s: pads without a net entry %s" % (p["ref"], extra))
        if p["ref"].startswith(("TP", "H")):
            fp.Value().SetVisible(False)
        if p["ref"].startswith("H"):
            fp.Reference().SetVisible(False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.12))
        board.Add(fp)

    # Pads the schematic marks "no connect" get KiCad's own unconnected-net names,
    # read from the schematic netlist, and every other pad is cross-checked against it.
    import xml.etree.ElementTree as ET
    sch = {}
    for n in ET.parse(NETLIST).getroot().iter("net"):
        for node in n.iter("node"):
            sch[(node.get("ref"), node.get("pin"))] = n.get("name").lstrip("/")
    bad = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            key = (fp.GetReference(), pad.GetNumber())
            if not pad.GetNumber():
                continue
            want = sch.get(key)
            have = pad.GetNetname()
            if want and want.startswith("unconnected-") and not have:
                pad.SetNet(net(want))
            elif (want or "") != have:
                print("NET MISMATCH", key, "schematic:", want, "board:", have)
                bad += 1
    if bad:
        raise SystemExit("board and schematic netlists disagree")
    board.BuildListOfNets()
    pcbnew.SaveBoard(path, board)
    board = pcbnew.LoadBoard(path)
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    print("placed", len(D.PARTS), "parts,", len(nets), "nets")


def pour_ground(board):
    gnd = board.FindNet("GND")
    # ground pour on both layers
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetAssignedPriority(0)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((0, 0), (D.BOARD_W, 0), (D.BOARD_W, D.BOARD_H), (0, D.BOARD_H)):
            o.Append(mm(OX + x), mm(OY + y))
        z.SetLocalClearance(mm(0.25))
        z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        board.Add(z)



def stitch(board, pitch=3.0, margin=0.9):
    """Add GND vias wherever both layers have ground pour with room to spare."""
    gnd = board.FindNet("GND")
    zones = list(board.Zones())
    tracks = list(board.GetTracks())
    pads = [p for f in board.GetFootprints() for p in f.Pads()]
    count = 0
    y = 1.5
    while y < D.BOARD_H - 1:
        x = 1.5
        while x < D.BOARD_W - 1:
            ok = True
            for dx, dy in ((0, 0), (margin, 0), (-margin, 0), (0, margin), (0, -margin),
                           (margin, margin), (-margin, -margin), (margin, -margin), (-margin, margin)):
                p = pt(x + dx, y + dy)
                if not all(z.HitTestFilledArea(z.GetLayer(), p, 0) for z in zones):
                    ok = False
                    break
            c = pt(x, y)
            if ok:
                for t in tracks:
                    if t.HitTest(c, mm(0.3 + 0.35)):
                        ok = False
                        break
            if ok:
                for pad in pads:
                    bb = pad.GetBoundingBox()
                    bb.Inflate(mm(0.7))
                    if bb.Contains(c):
                        ok = False
                        break
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pt(x, y))
                v.SetWidth(pcbnew.F_Cu, mm(0.6))
                v.SetDrill(mm(0.3))
                v.SetNet(gnd)
                board.Add(v)
                count += 1
            x += pitch
        y += pitch
    return count


def finish(path, ses):
    board = pcbnew.LoadBoard(path)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    pour_ground(board)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    n = stitch(board)
    filler.Fill(board.Zones())
    print("ground stitching vias:", n)
    pcbnew.SaveBoard(path, board)
    tracks = [t for t in board.GetTracks()]
    vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
    print("routed: %d track segments, %d vias" % (len(tracks) - vias, vias))


if __name__ == "__main__":
    {"place": place, "finish": finish}[sys.argv[1]](sys.argv[2], sys.argv[3])
