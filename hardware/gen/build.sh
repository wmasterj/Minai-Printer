#!/bin/bash
# Regenerate the KiCad project and manufacturing outputs from design.py.
#
# Needs: Docker (image kicad/kicad:9.0), Java 17+, and the Freerouting jar
# (https://github.com/freerouting/freerouting/releases, tested with v2.0.1).
#
#   FREEROUTING_JAR=/path/to/freerouting.jar hardware/gen/build.sh          # schematic + outputs only
#   FREEROUTING_JAR=/path/to/freerouting.jar hardware/gen/build.sh --route  # also re-place and re-route the board
#
# Re-routing is not deterministic: every run gives a different layout, and a
# run can end with unrouted nets or a short. Check drc-report.txt after each
# run and re-run (or nudge PCB_POS in design.py) until it is clean.
set -euo pipefail
cd "$(dirname "$0")/../.."
IMG=${KICAD_IMAGE:-kicad/kicad:9.0}
TMP=${TMPDIR:-/tmp}/minai-build
mkdir -p "$TMP/home/kcfg/9.0"
K() { docker run --rm -u 0 -e HOME=/scratch/home -e KICAD_CONFIG_HOME=/scratch/home/kcfg \
        -v "$PWD":/work -v "$TMP":/scratch -w /work "$IMG" "$@"; }
K bash -c 'cp -n /usr/share/kicad/template/*-lib-table /scratch/home/kcfg/9.0/'

SCH=hardware/kicad/minai-printer.kicad_sch
PCB=hardware/kicad/minai-printer.kicad_pcb
OUT=hardware/outputs

K python3 hardware/gen/gen_sch.py $SCH
K kicad-cli sch export netlist --format kicadxml -o /scratch/sch.net.xml $SCH

if [ "${1:-}" = "--route" ]; then
  rm -f $PCB "$TMP/board.ses"
  K python3 hardware/gen/gen_pcb.py place $PCB /scratch/board.dsn
  (cd "$TMP" && java -Djava.awt.headless=true -jar "$FREEROUTING_JAR" \
      -de board.dsn -do board.ses -mp 100 --gui.enabled=false > freerouting.log 2>&1)
  K python3 hardware/gen/gen_pcb.py finish $PCB /scratch/board.ses
fi

K bash -c "
set -e
kicad-cli sch erc --severity-all -o $OUT/erc-report.txt $SCH
kicad-cli pcb drc --severity-all --schematic-parity -o $OUT/drc-report.txt $PCB
kicad-cli sch export pdf -o $OUT/schematic.pdf $SCH
mkdir -p $OUT/gerbers && rm -f $OUT/gerbers/*
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o $OUT/gerbers/ $PCB
kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format pdf -o $OUT/gerbers/ $PCB
kicad-cli pcb export pos --format csv --units mm --side front -o $OUT/pick-and-place.csv $PCB
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,Edge.Cuts -o $OUT/board-top.pdf $PCB
kicad-cli pcb export pdf --layers B.Cu,Edge.Cuts -o $OUT/board-bottom.pdf $PCB
kicad-cli pcb render --side top --width 1800 --height 1500 -o $OUT/board-3d-top.png $PCB
kicad-cli pcb render --side bottom --width 1800 --height 1500 -o $OUT/board-3d-bottom.png $PCB
python3 hardware/gen/gen_bom.py $OUT
chmod -R a+rw hardware
"
(cd $OUT/gerbers && rm -f ../gerbers.zip && zip -q ../gerbers.zip *)
rm -f hardware/kicad/*.kicad_prl hardware/kicad/fp-info-cache
grep -h "Found\|ERC messages" $OUT/drc-report.txt $OUT/erc-report.txt
