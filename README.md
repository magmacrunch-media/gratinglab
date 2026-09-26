# gratinglab

[![ci](https://github.com/magmacrunch-media/gratinglab/actions/workflows/ci.yml/badge.svg)](https://github.com/magmacrunch-media/gratinglab/actions/workflows/ci.yml)

> **There are two repositories called `gratinglab`, and they are not the same
> thing.** This one — `magmacrunch-media/gratinglab` — is the *application*.
> [`jamccoy/gratinglab`](https://github.com/jamccoy/gratinglab) is the Python
> package it ports, and remains the reference implementation and the source of
> truth for every formula here. Same project, two halves, two accounts.

Diffraction from a grating in the **extreme off-plane (conical) mount**, at
grazing incidence — the geometry soft X-ray reflection-grating spectrometers
use, and the one no optics app on the store draws.

Orbit the cone, then pull **rim focus**: at γ = 1.5° the cone of diffraction is
a needle 0.00° wide in polar angle and a fan 93.8° wide in azimuth, both at
once, and that combination is precisely what a dispersion-plane drawing cannot
convey. Uniform zoom is a similarity transform, so the fan opens up without a
single angle being exaggerated.

The application's own name is nowhere in the code — no prefix, no bundle string
carries it — so what it ends up being called on a store is still open.

## What it computes

A JavaScript port of the scalar (Kirchhoff / thin-element) solver from
[gratinglab](https://github.com/jamccoy/gratinglab), which is the reference
implementation and stays the source of truth.

- **Geometry** — the generalized grating equation, `sin α + sin β_m = mλ/(p sin γ)`,
  order bookkeeping, evanescent orders drawn as passing off rather than dropped.
- **Two parameterisations of the same mount**: `(γ, α)`, the cone angles the
  diffraction is written in, or `(η, φ)`, the principal axes a stage is actually
  set to: `sin η = sin γ cos α` and `sin φ = tan α tan η` (McCoy et al. 2020).
  `η` is the pitch angle *and* the graze angle onto the substrate: one number,
  two names. `φ` is yaw, measured from the groove direction, so `φ = 0` is
  an exact off-plane mount and `φ = 90°` an exact in-plane one. Turning the
  grating about its own normal at fixed pitch opens the cone:
  `sin²γ = sin²η + sin²φ cos²η`. Roll `ϕ` is the third axis and **adds to `α`**:
  it turns the grating about the groove axis, which `γ` cannot see, so
  `α = α(η, φ) + ϕ`. Set against a mount that is not level, the stage pitch and
  the graze the surface actually sees come apart, and the app shows both.
  `α = 0`, `φ = 0` and `η = γ` are one condition, the exact off-plane mount,
  whose `γ = 90°` end is normal incidence: `k̂ᵢ = −n̂`, `sin β_m = mλ/p`, and no
  azimuth left to turn.
- **Reflection and transmission** — the same grating equation governs both, and
  the propagation test `|sin β_m| ≤ 1` never mentions the branch, so **exactly
  the same orders propagate on each side**. A transmitted order is distinguished
  only by `cos β_m < 0`, which puts it on the same cone mirrored through the
  surface. Show either branch or both.
- **Efficiency** — `E_m = O_m |G_m|²` from the general Fourier integral, with
  the *symmetric* flux obliquity `4 cos α cos β_m / (cos α + cos β_m)²`, so
  Lorentz reciprocity survives. ΣE is reported and **never renormalised**: the
  deviation from unity is the model's own error signal.
- **Coatings** — Au from a CXRO/Henke table. Naming a coating is what turns the
  numbers absolute. All three of the package's reflectivity models are here:

  | model | what it does | reciprocal |
  |---|---|---|
  | `local` | complex Fresnel amplitude at every quadrature point, carried *inside* the integral and weighted by the geometric mean of the incident and exit reflectivities — so reflectivity is **order-dependent** | yes |
  | `average` | `⟨R(ζ(t))⟩` over the whole period, one factor per wavelength | no |
  | `facet` | one `R` at the active-facet angle, applied to every order alike | no |

  Only `local` symmetrises in the exit direction, which is what keeps Lorentz
  reciprocity; the other two build `ζ` from `α` alone. The app reports all three
  sums together, so the size of each approximation is measurable rather than
  asserted — about −0.8% and −0.6% at the reference geometry.
- **Broadband** — open the band and each order smears into a spectrum along the
  cone rim. Since `sin β` depends on `m` and `λ` only through their product,
  order `m` at `λ` and order `m+1` at `mλ/(m+1)` leave in the same direction.
  The dispersion strip shows that overlap, and its `arc` lane is what a detector
  sweeping the arc actually sees.

## What it does not

**No transmitted efficiency.** The ported solver is a reflection-grating model,
so transmitted orders carry a direction and nothing else — they are drawn dashed
and at uniform width precisely so their thickness cannot be read as one. The
package's integral solver does compute transmission, with `R + T = 1`, and it is
not ported.

No rigorous method. The integral solver needs dense complex linear algebra and
is not ported, so there is nothing here to cross-check a per-order number
against — which matters, because the default geometry already trips
gratinglab's reduced-ratio guard. Also absent: roughness (Névot–Croce and
Debye–Waller both), the Brewster crossing check, the `average` and `facet`
reflectivity models, horizon visibility, and every material but gold.

All of that is stated in the app's own provenance panel rather than left
implied. A validity limit and an expected deviation are marked differently
there, because they mean opposite things.

## Checking it

```bash
node tools/check.mjs
```

Extracts the physics straight out of `app/index.html` and compares it to
`tools/fixture.json`: 722 propagating orders across 19 geometries, bare and
gold, and every reflectivity model. Agreement is to 2.6e-13 relative; the
tolerance is 1e-9. Needs node and nothing else.

`tools/ref.py` regenerates the fixture and is the only thing that needs Python,
numpy, pydantic and a checkout of the package. It finds one by `$GRATINGLAB`,
then `../gratinglab`, then `../../../jamccoy/gratinglab` — skipping any
candidate that resolves to this repo, which is called gratinglab too.

CI runs the same comparison twice, and the pair is diagnostic rather than
redundant: `check` holds the page to the committed fixture, and `fixture`
regenerates it from `jamccoy/gratinglab` at `main` first. So `check` red means
the port moved, and `check` green with `fixture` red means the package did and
`tools/fixture.json` wants regenerating.

## Layout

```
app/index.html   the whole application, one file
tools/check.mjs  conformance check, node only
tools/ref.py     regenerates tools/fixture.json from gratinglab
tools/embed_materials.py   re-embeds the Au table at full precision
```

## Licence

The port and this application are © magmacrunch media. gratinglab is
BSD-3-Clause by Jake McCoy; the optical constants are a CXRO/Henke export.
