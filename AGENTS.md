# AGENTS.md — gratinglab (the app)

A magmacrunch app whose physics comes from a **jamccoy** repo of the same name.
That split is the one thing to understand before changing anything here.

## Two repositories are called gratinglab

| | |
|---|---|
| `dev\jamccoy\gratinglab` | the **package**. Python, numpy, pydantic, a 15,000-line test suite. Public, BSD-3, `jamccoy/gratinglab`. The reference implementation and the source of truth for every formula. |
| `dev\magmacrunch\apps\gratinglab` | **this repo, the app**. One HTML file, a JavaScript port of one solver out of that package. `magmacrunch-media/gratinglab`. |

The name is shared on purpose — it is one project — but the two are different
artifacts on different accounts, and a reference to "gratinglab" in any note is
ambiguous unless it says which. Prefer "the package" and "the app".

The concrete trap: **`../gratinglab` from this repo is this repo**, since it
sits in `apps\` beside its siblings. `tools/ref.py` therefore rejects any
candidate that resolves to its own root before falling through to
`../../../jamccoy/gratinglab`. Do not simplify that check away.

The two accounts are kept apart on disk and in git identity (see
`dev\CLAUDE.md`), and **nothing here may depend on the jamccoy checkout at run
time or at check time.**

`tools/fixture.json` is what buys that. It is generated once from the real
`ScalarSolver` and committed, so `node tools/check.mjs` runs anywhere with node
alone. Only `tools/ref.py` — run by hand when the solver changes — needs Python
and a gratinglab checkout, and it locates one by `$GRATINGLAB`, then
`../gratinglab`, then `../../../jamccoy/gratinglab`.

**Commits here are magmacrunchmedia**, from the global git config. Do not set
`user.email` in this repo; the conditional include in `~/.gitconfig` only
redirects paths under `dev\jamccoy\`, and a local override would defeat it.

## A second implementation is the hazard this repo is built around

The port is arithmetic that already exists, written a second time in another
language. That drifts. Everything below is arranged to make drift loud:

- `tools/check.mjs` **extracts the physics out of `app/index.html` by text**,
  between `  function sinBeta(` and `  function scene(){`, and evaluates that.
  It tests the code that ships, not a copy. Rename or move those functions and
  the check fails loudly with the anchors it looked for — which is correct, and
  is why the anchors are stated in the error rather than left to be guessed.
- The tolerance is **1e-9 relative**, far tighter than anything the interface
  could show. That is deliberate. The port is the same arithmetic in the same
  order, so real agreement is at float noise (2.6e-13 today) and anything above
  it is a genuine difference.

**It has already caught the bug it exists for.** The first coated run failed at
1.8e-6. The cause was `tools/embed_materials.py` emitting the Au table at six
significant figures: δ ≈ 0.0112813823 lost its tail, every absolute efficiency
in the app was wrong in the seventh digit, and nothing visible in the
application would ever have shown it. Emit full precision.

## Physics conventions, which are gratinglab's

`docs/conventions.md` in gratinglab is normative. The three that bite:

- **d̂ = +x, n̂ = +y, ĝ = −z**, and the cone opens along **−ĝ**, not ĝ. Every
  wave vector carries `k_z = +k cos γ`. Opening it the other way points every
  ray 180° out.
- `k̂(β) = (sin γ sin β, sin γ cos β, cos γ)`, and the incident vector is
  `(−sin γ sin α, −sin γ cos α, cos γ)` — it travels *toward* the grating.
- **ζ is measured from the surface**, not from the normal, in both
  `facet_graze` and the Fresnel layer, so they compose with no conversion.
  Taking the other sense is a silent 90° error that still returns numbers
  in [0, 1].

Two signs are load-bearing and neither is obvious:

- `tan δ(t) = +dy/dt` in **normalised** units for the facet tilt. The profile
  parameter runs against the periodicity direction, which makes the other sign
  look equally plausible; it is wrong. An ideal sawtooth must come back with δ
  equal to its own blaze angle everywhere.
- The Fresnel `k2 = sqrt(n² − cos²ζ)` takes the **principal branch**, so the
  transmitted wave decays. The other branch grows with depth and gives a
  reflectivity above one.

## The obliquity factor is the symmetric one

`O_m = 4 cos α cos β_m / (cos α + cos β_m)²`, **not** the `cos β_m / cos α` of
the thesis Appendix D. The asymmetric form breaks reciprocity; only the
symmetric one reproduces first-order perturbation theory in the shallow limit.
And ΣE is reported, never rescaled — renormalising to 1 (as Appendix D does)
destroys the model's own signal about how far it has strayed.

If either of those is ever "fixed", the fixture will disagree, which is the
point.

## CI answers two questions, not one

`check` holds `app/index.html` to the committed `tools/fixture.json`, with node
alone. `fixture` regenerates that file from `jamccoy/gratinglab` at `main` and
runs the identical comparison against the result. Read the pair:

| | |
|---|---|
| `check` red | the port changed, or broke |
| `check` green, `fixture` red | the package moved; rerun `tools/ref.py` and commit the new fixture |
| both red | look at `check` first |

The second job compares **numerically at the 1e-9 tolerance**, not by diffing
JSON. A byte comparison would also fire on a last-bit difference in whichever
numpy the runner installed, which is noise, and would report it as though the
physics had changed.

The package is checked out at `main` rather than a pinned ref, for the reason
nanofab-simulator pins nothing on hologram. And note CI passes `$GRATINGLAB`
rather than using the flat `../gratinglab` layout, because with both repos
called gratinglab that layout cannot exist — one would have to sit inside the
other.

`tools/ref.py` sets `sys.stdout.reconfigure(newline="\n")`, so the documented
`> tools/fixture.json` redirect writes LF on Windows too. Without it the file
comes out CRLF there, `.gitattributes` normalises it away at commit, and the
result is a working tree that silently disagrees with its own index.

## Rebuilding the Au table

```bash
python tools/embed_materials.py && node tools/check.mjs
```

The table is inlined in `app/index.html` on purpose: the page has to stay a
single file for the iOS bundle. 500 rows, 0.620–6.199 nm, and **outside that
range the app computes nothing** rather than extrapolating, matching
`OpticalConstants._require_in_range` raising.

## Name

The repo **and the application** are both `gratinglab`, matching the package it
ports. Decided 2026-09-22. It was `OFF//PLANE` for one commit, in the house
style of `BOT//FARM` and `CRUNCH//SCOPE`; that name is free if a store listing
ever wants something other than the package's.

The name still appears nowhere in the code — no prefix, no bundle string, no
page title carries it — so this is a decision that stays cheap to revisit.

The bundle id is the part that becomes permanent, at the first submission, and
it is the one open decision: `com.magmacrunch.*` ties this to the org the way
CRUNCH//SCOPE is tied, and `com.jamccoy.*` would mean a second App Store Connect
arrangement.
