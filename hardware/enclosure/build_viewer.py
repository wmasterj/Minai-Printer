"""Insert out/meshes.json into the viewer template -> viewer.html (open it in any browser)."""
import os
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "viewer.template.html")).read()
m = open(os.path.join(here, "out", "meshes.json")).read()
open(os.path.join(here, "viewer.html"), "w").write(t.replace("/*MESHES*/", m))
print("wrote viewer.html", len(t) + len(m), "bytes")
