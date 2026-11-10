"""Write the bill of materials (CSV + Markdown) from design.py. Plain Python, no KiCad needed."""
import csv
import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))
import design as D

OUT = sys.argv[1]

# Manufacturer pages / datasheets for the parts that matter.
DOCS = {
    "ESP32-C3-WROOM-02-N4": "https://www.espressif.com/en/products/modules/esp32-c3",
    "DRV8833PWR": "https://www.ti.com/product/DRV8833",
    "AP2112K-3.3TRG1": "https://www.diodes.com/part/view/AP2112",
    "USBLC6-2SC6": "https://www.st.com/en/protection-devices/usblc6-2.html",
    "74LVC2G04GW": "https://www.nexperia.com/product/74LVC2G04GW",
}


def search_key(p):
    if p["mpn"]:
        return p["mpn"].split(" ")[0].split("/")[0]
    if p["ref"][0] in "RC":          # generic passive: search by value and package
        size = p["fp"].split(":")[1].split("_")[1]
        kind = "resistor" if p["ref"][0] == "R" else "capacitor"
        return "%s %s %s" % (p["value"].replace(" 1%", ""), size, kind)
    return ""


groups = {}
for p in D.PARTS:
    if not p.get("bom", True):
        continue
    key = (p["value"], p["fp"], p["mpn"])
    g = groups.setdefault(key, dict(refs=[], part=p))
    g["refs"].append(p["ref"])


def refkey(r):
    head = r.rstrip("0123456789")
    return (head, int(r[len(head):]))


rows = []
for (value, fp, mpn), g in groups.items():
    p = g["part"]
    k = search_key(p)
    lcsc = "https://www.lcsc.com/search?q=" + quote(k) if k else ""
    digi = "https://www.digikey.com/en/products/result?keywords=" + quote(k) if k else ""
    rows.append(dict(refs=sorted(g["refs"], key=refkey), qty=len(g["refs"]), value=value,
                     desc=p["desc"], footprint=fp.split(":")[1], mfr=p["mfr"], mpn=mpn,
                     lcsc=lcsc, digikey=digi, doc=DOCS.get(k, "")))
rows.sort(key=lambda r: refkey(r["refs"][0]))

with open(os.path.join(OUT, "bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designators", "Qty", "Value", "Description", "Footprint", "Manufacturer",
                "Part number", "LCSC search", "DigiKey search", "Manufacturer page"])
    for r in rows:
        w.writerow([" ".join(r["refs"]), r["qty"], r["value"], r["desc"], r["footprint"],
                    r["mfr"], r["mpn"], r["lcsc"], r["digikey"], r["doc"]])

with open(os.path.join(OUT, "bom.md"), "w") as f:
    f.write("| Designators | Qty | Value | Description | Part number | Links |\n")
    f.write("|---|---|---|---|---|---|\n")
    for r in rows:
        links = []
        if r["doc"]:
            links.append("[maker](%s)" % r["doc"])
        if r["lcsc"]:
            links.append("[LCSC](%s)" % r["lcsc"])
            links.append("[DigiKey](%s)" % r["digikey"])
        f.write("| %s | %d | %s | %s | %s | %s |\n" % (
            " ".join(r["refs"]), r["qty"], r["value"], r["desc"], r["mpn"] or "generic",
            " · ".join(links)))
print("BOM lines:", len(rows), "placements:", sum(r["qty"] for r in rows))
