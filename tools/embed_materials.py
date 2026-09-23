"""Re-embed gratinglab's vendored Au table into app/index.html.

    python tools/embed_materials.py

Rarely needed: only when the table itself changes. Run it and then
`node tools/check.mjs`, which is what catches a mistake here.

**Emit full precision.** The first version of this script wrote six significant
figures, which put a 1e-6 relative error on every coated efficiency in the app.
That is invisible in the interface and wrong in every number it prints; the
conformance check is the only thing that saw it.
"""
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ref import find_gratinglab  # noqa: E402

sys.path.insert(0, str(find_gratinglab()))
from gratinglab import materials  # noqa: E402

PAGE = HERE.parent / "app" / "index.html"
SIG = 17  # round-trips a float64


def column(values):
    return ",".join(("%.*g" % (SIG, v)) for v in values)


au = materials.lookup("Au")
block = (
    "  // CXRO/Henke export Au.txt, vendored from gratinglab.materials.\n"
    "  // Ascending in wavelength, %.4f to %.4f nm, %d rows.\n"
    "  var AU = {\n"
    "    name:\"Au\",\n"
    "    wl:[%s],\n"
    "    d:[%s],\n"
    "    b:[%s]\n"
    "  };"
) % (
    au.range_nm[0],
    au.range_nm[1],
    len(au.wavelength_nm),
    column(au.wavelength_nm),
    column(au.decrement),
    column(au.absorption),
)

html = io.open(PAGE, encoding="utf-8").read()
pattern = re.compile(r"  // CXRO/Henke export Au\.txt.*?\n  \};", re.DOTALL)
new, n = pattern.subn(lambda _: block, html, count=1)
if n != 1:
    raise SystemExit(f"expected exactly one AU table block in {PAGE}, found {n}")

io.open(PAGE, "w", encoding="utf-8", newline="").write(new)
print(f"embedded {len(au.wavelength_nm)} rows into {PAGE}")
