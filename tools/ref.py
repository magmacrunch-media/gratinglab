"""Regenerate tools/fixture.json from gratinglab's own ScalarSolver.

    python tools/ref.py > tools/fixture.json

This is the only step that needs Python, numpy, pydantic and a gratinglab
checkout. `tools/check.mjs` reads the committed fixture and needs none of them,
which is what keeps this repo independent of the jamccoy tree.

The package is found by $GRATINGLAB, then ../gratinglab, then
../../../jamccoy/gratinglab -- the same order the rest of this tree uses for a
sibling engine, so both a flat clone and the grouped layout work.

Note that this repo is *also* called gratinglab, so `../gratinglab` can resolve
to this repo's own root. A candidate is accepted only if it holds
src/gratinglab/__init__.py and is not this repo, which is why the second test is
there.

Au is tabulated 0.620-6.199 nm, so every coated case sits inside that range.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def find_gratinglab() -> Path:
    candidates = []
    env = os.environ.get("GRATINGLAB")
    if env:
        candidates.append(Path(env))
    candidates.append(REPO.parent / "gratinglab")
    candidates.append(REPO.parent.parent.parent / "jamccoy" / "gratinglab")
    for candidate in candidates:
        # This repo is called gratinglab too, so the sibling candidate can be
        # this very directory. It has no src/gratinglab/, but say so explicitly
        # rather than relying on that.
        if candidate.resolve() == REPO:
            continue
        if (candidate / "src" / "gratinglab" / "__init__.py").is_file():
            return candidate / "src"
    raise SystemExit(
        "the gratinglab PACKAGE was not found (this repo is the app of the same "
        "name). Tried:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\nSet GRATINGLAB=<path to the jamccoy/gratinglab checkout>."
    )


sys.path.insert(0, str(find_gratinglab()))

from gratinglab.illumination import Illumination  # noqa: E402
from gratinglab.problem import Problem  # noqa: E402
from gratinglab.profiles import Blazed  # noqa: E402
from gratinglab.solvers.scalar import ScalarSolver  # noqa: E402

#: Chosen to exercise what the port actually does, not to be tidy: the
#: reference off-plane mount, a shallow blaze where the sum runs *above* unity,
#: a near-classical mount, a cone steep enough to put the local graze past the
#: critical angle, and one case with enough orders to catch a Nyquist mistake.
CASES = [
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=3.0, blaze=29.5, coat=False),
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=3.0, blaze=8.0, coat=False),
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=6.0, blaze=29.5, coat=False),
    dict(period=315.15, alpha=25.0, gamma=12.0, lam=3.0, blaze=29.5, coat=False),
    dict(period=1000.0, alpha=10.0, gamma=60.0, lam=50.0, blaze=15.0, coat=False),
    dict(period=600.0, alpha=-40.0, gamma=89.0, lam=120.0, blaze=22.0, coat=False),
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=3.0, blaze=29.5, coat=True),
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=1.2, blaze=29.5, coat=True),
    dict(period=315.15, alpha=25.0, gamma=1.5, lam=6.0, blaze=8.0, coat=True),
    dict(period=315.15, alpha=25.0, gamma=3.0, lam=2.0, blaze=29.5, coat=True),
    dict(period=315.15, alpha=25.0, gamma=12.0, lam=3.0, blaze=29.5, coat=True),
    dict(period=600.0, alpha=5.0, gamma=45.0, lam=4.0, blaze=12.0, coat=True),
    dict(period=1000.0, alpha=15.0, gamma=2.0, lam=0.9, blaze=3.0, coat=True),
]

#: The port's default. Must match, or every number differs by the quadrature
#: error rather than by anything the check is looking for.
QUADRATURE_POINTS = 1024

out = []
solver = ScalarSolver()
for case in CASES:
    problem = Problem(
        period=case["period"],
        profile=Blazed(blaze_angle=case["blaze"], antiblaze_angle=90.0),
        coating="Au" if case["coat"] else None,
    )
    illumination = Illumination(alpha_deg=case["alpha"], gamma_deg=case["gamma"])
    scan = solver.solve(
        problem, illumination, [case["lam"]], quadrature_points=QUADRATURE_POINTS
    )
    rows = [
        {"m": int(m), "E": float(scan.efficiency[0, j])}
        for j, m in enumerate(scan.orders)
        if scan.propagating[0, j]
    ]
    out.append(
        {"case": case, "orders": rows, "sum": float(sum(r["E"] for r in rows))}
    )

print(json.dumps(out, indent=1))
