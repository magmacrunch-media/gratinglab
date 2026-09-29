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

## The App Store bundle

`node ios/package.mjs` builds `ios/www/` from `app/`, on hypnopompia's shared
pipeline. Bundle id **`com.magmacrunch.gratinglab`**, chosen 2026-09-25 and
permanent from the first submission. Capacitor uses SPM here, not CocoaPods, so
there is no `pod install`.

**There is exactly one thing wrong with `app/index.html` in a bundle**: it asks
Google for IBM Plex. The script vendors the five faces the page actually sets
(Plex Sans 400/500/600, Plex Mono 400/500) from `@fontsource` and rewrites the
request into a local `@font-face` block. Everything else is already
self-contained, which the CI guard keeps true. The bundle is 232 KB, 124 of it
fonts, and `b.sweepSelfContained()` refuses it if anything reaches outside or
over the network.

`createBuild` is called with **no `probe`**. Every other consumer vendors files
from the website repo and passes one; this page reads nothing from it. That is
hypnopompia `8a73ddf`, which made the website lookup lazy for this consumer, so
**push hypnopompia before a gratinglab commit that needs it**, as with any
engine. Do not call `transforms.viewportNotch`: the page already declares
`viewport-fit=cover`, the transform would be a no-op, and the pipeline's
contract is that a no-op edit is fatal.

**The page owns its safe areas.** `contentInset` is `"never"` and there is no
browser chrome in an app, so without `--sat`/`--sab`/`--sal`/`--sar` on `:root`
the title runs under the Dynamic Island. `env()` only reports real numbers
because the viewport meta carries `viewport-fit=cover` — the same meta whose
absence broke the phone layout entirely.

Building and running it on the simulator, from this machine. `$MACHOST` is the
build host, which `dev\CLAUDE.md` names; this repo is public and does not:

```bash
scp -r ios/App "$MACHOST":~/glbuild/App
# on the Mac, with DEVELOPER_DIR set (see below):
cd ~/glbuild/App/App && xcodebuild -project App.xcodeproj -scheme App \
  -sdk iphonesimulator -destination "platform=iOS Simulator,name=iPhone 17 Pro" \
  -derivedDataPath ~/glbuild/dd CODE_SIGNING_ALLOWED=NO build
xcrun simctl install booted ~/glbuild/dd/Build/Products/Debug-iphonesimulator/App.app
xcrun simctl launch booted com.magmacrunch.gratinglab
```

## The viewer

One finger orbits. Two fingers carry three channels at once -- pan from the
centroid, zoom from the separation, **roll from the twist** -- and the wheel
zooms about the cursor. Recentre, or a double tap, clears all of it.

Roll is a third rotational freedom the yaw/pitch orbit cannot reach, and it is
what lets the azimuth fan lie flat on the screen instead of across a diagonal.

**The WebView will take two-finger input before the page ever sees it**, and
that is the first thing to suspect when a gesture "does nothing". Three
defences, all needed:

- `maximum-scale=1, user-scalable=no` in the viewport meta. `touch-action`
  alone has never been reliable against iOS pinch-zoom.
- `touch-action:none` on **`#sky`**, not only on `#stage`. It is not inherited,
  and the touch lands on the canvas.
- `preventDefault` on `gesturestart`/`gesturechange`/`gestureend`, which WebKit
  fires alongside the pointer events and which actually perform the page scale.

The cost is that the page can no longer be pinch-zoomed as a document. That is
right for the app, which has its own zoom on two axes, and it is the same trade
every Capacitor app makes.

**Synthetic PointerEvents cannot catch this.** Dispatching at the stage bypasses
the browser's gesture handling entirely, so the harness proved the arithmetic
and said nothing about whether a real finger ever arrives. Both were true at
once for a while: the pinch anchor was measured correct -- two pinches about
different points land 1100 device px apart -- while on the device two fingers
did nothing at all.

**Each channel has a deadband, and that is what keeps them apart.** Two fingers
never move in perfect sympathy, so without one a pan arrives carrying a few per
cent of zoom and a degree or two of roll, and the gesture stops feeling like the
one thing it was meant to be. Pan is always live; zoom needs 8% of separation
and roll needs 7 degrees before either engages. Crossing a deadband re-zeroes
**every** channel, not just the one that fired, because `zoomAbout` reads
`g.cx`, `g.upx` and `g.uz` as one consistent baseline -- and rebasing stops the
scene jumping by the whole deadband at the moment of engagement. `S.uz/upx/upy` sit on
top of the fitted framing; the rim slider and the fit decide everything else, so
Recentre never disturbs the orbit or the rim.

Three things here are not obvious and all three were found by driving synthetic
`PointerEvent`s at the stage and reading back what the page displays:

- **Rebaseline on every change in contact count.** Written off a single
  remembered start point, the scene jumps the instant a second finger lands or
  the first lifts.
- **Clamp the zoom first, then pan by the factor actually applied.** Using the
  requested factor makes the content slide out from under the fingers at the
  limits.
- **Two fingers lifting are two `pointerup`s a few milliseconds apart.** A naive
  "was the last up recent" double-tap test fires at the end of every pinch and
  throws the zoom away. A tap has to be one contact, brief and still, which is
  what `tapDown/tapMove/tapUp` enforce.

`viewRect()` is the other half. It measures the overlays rather than assuming
their size, because they are drawn *over* the canvas -- so the geometric centre
of the canvas is not the centre of what you can see, and centring on it put the
scene behind the title block. **Take a rect only when it has a size**: a
`display:none` element reports zeros, not nothing, and hiding the caption on a
short screen once pulled the bottom edge to -8 and floored the whole view box at
80px, making the scene smaller for being given more room.

On a short screen the caption and the subtitle are hidden. They cost about a
third of the usable height in landscape, and the provenance panel carries the
same statements.

## The app icon

`python scripts/make-icon.py` writes both appearances into the icon set; it
needs Pillow. The drawing is a blazed grating throwing its orders, which is the
app with everything removed that will not survive 60 points.

Two things inherited from crunchscope and george-boole, and both are the point:

- **A dark subject on a dark ground is a blob at home-screen size.** This app's
  own ground is nearly black, so the gold band is what gives the icon a
  silhouette and everything else is drawn on top of it.
- **Judge it small.** `--sheet out.png` writes 60, 120 and 180 pixel copies,
  masked to the iOS shape, on a light and a dark wallpaper. At 1024 everything
  looks fine, so 1024 is not an opinion worth having. The first draft had five
  shallow teeth that read as battlements and two rays 6 degrees apart that read
  as a mistake; only the sheet showed either.

There is a dark-appearance variant because from iOS 18 the system dims a light
icon on a dark home screen, which takes gold towards brown. It is drawn on a
deeper ground with a brighter band.

## The launch screen

`python ios/tools/make-splash.py` writes the three square files Capacitor's
imageset names; `--crops out.png` renders what each device actually shows. It
needs Pillow, and a website checkout for the publisher mark -- the only thing in
this repo that does, and deliberately not `ios/package.mjs`.

**Both axes crop here, which is the difference from every other app in the
tree.** `LaunchScreen.storyboard` aspect-fills one square, so the view's shorter
side decides how much survives on that axis: a portrait view keeps `W/H` of the
width, a landscape view keeps `H/W` of the height. `Info.plist` allows portrait
*and* both landscapes on the phone, so both happen, and both at 0.460. crunchscope
is portrait-only and therefore only ever loses width.

So anything that must be seen lives in the central 46% square. The grating band
and the rays run past it and get cut, which is what they do in the app too; the
mark does not, and `draw_splash()` asserts it rather than trusting the eye.

`CROP_WIDTH` and `CROP_HEIGHT` are module-level constants because
`hypnopompia/tools/check-launch-crop.mjs` reads those names and ties them to the
orientations in `Info.plist`. Run it after any change to either:

```bash
node ../../engines/hypnopompia/tools/check-launch-crop.mjs ../../apps/gratinglab/ios
```

That is also why this script sits in `ios/tools/` while `make-icon.py` sits in
`scripts/`: the checker's contract names `ios/tools/`, and being covered by an
existing guard beat keeping the two scripts together.

## PWA

The app ships as a Progressive Web App. Three files in `app/`:

| file | purpose |
|---|---|
| `manifest.json` | name, colours, icons, `display: standalone` |
| `sw.js` | service worker — cache-first for the app shell, stale-while-revalidate for Google Fonts |
| `icons/` | 192×192 and 512×512 PNGs, generated by `python3 scripts/make-icon.py --pwa app/icons` |

`index.html` carries `<meta name="theme-color">`, `<link rel="manifest">`, and
the one-line SW registration at the bottom of `<body>`. The iOS bundle's
`package.mjs` strips the SW registration (a native app has no service worker)
and leaves the manifest and theme-color in place — Capacitor reads both.

The precache list in `sw.js` must match the files `index.html` actually loads.
If a new CSS or JS file is added to the page and not to the precache, the
worker serves stale bytes for everything it does cover and fetches the new
file fresh — which works but defeats the offline guarantee. The cache version
string (`gratinglab-v1`) bumps when the precache set changes.

## The Mac checkout

There is a real clone at **`~/mc/gratinglab`** on the build host, beside
`hypnopompia`, `george-boole`, `makemecookies` and `website` — the same flat
layout the tree documents, so `ios/package.mjs` finds the pipeline at its second
candidate `../hypnopompia` with no override. Work in Xcode from there:

```bash
ssh "$MACHOST"
export PATH=/opt/homebrew/bin:$PATH          # node and npm are not on the
cd ~/mc/gratinglab/ios                       # non-interactive PATH otherwise
git -C .. pull && npm run sync && npm run open
```

**It authenticates with a read/write deploy key** reached through the
`gratinglab.github.com` alias in the Mac's `~/.ssh/config`. The Mac's
own key is not registered with GitHub and the osxkeychain credential does not
cover a private repo, so a plain HTTPS clone there fails asking for a username.

It started read-only, per the rule in `dev\CLAUDE.md` that a deploy key suits a
read of one repo, and was widened so the Mac can commit its own work rather than
round-tripping every change through the dev box. That rule is about CI reaching
across repos; a developer's own machine is a different case. The key is still
scoped to **this repo alone**, which is the part that matters, and revoking it is
one click at the repo's Settings → Deploy keys.

A deploy key cannot be edited in place: widening it means deleting the key and
adding the same public key again with `read_only=false`, which changes its id.

Commits made there are authored `magmacrunchmedia <magmacrunchmedia@gmail.com>`
from the Mac's own global config, so they match the dev box and need no per-repo
override. **Both machines can push now, so pull before working on either.**

**Pull hypnopompia there too.** The Mac's copy was three commits behind and
`package.mjs` died inside `createBuild` with
`The "path" argument must be of type string` — the old pipeline resolved a
website eagerly and joined an undefined `probe`, which is exactly the argument
this app does not pass. The flat-layout resolution was working perfectly; the
engine beside it was stale. A consumer that builds here and not there is the
failure the tree's push-the-engine-first rule exists for, seen from the other
end.

Do not point `-derivedDataPath` inside the checkout. Xcode's own default is
outside it; a scripted build that writes `ios/dd` leaves an untracked directory
nothing ignores.

## Running it on the iOS simulator

The Mac build host is reached by its IP rather than its hostname; `dev\CLAUDE.md`
has the address. Xcode is installed but `xcode-select` points at the Command Line Tools, so
`xcodebuild` and `simctl` both fail out of the box. Repointing it globally needs
`sudo`; export the variable instead and change nothing on that machine:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
```

There is no `ios/` project here yet, so the way to see the page on a phone is to
serve `app/` on the Mac and open it in the simulator's Safari:

```bash
scp app/index.html "$MACHOST":/tmp/glserve/index.html
# on the Mac, with DEVELOPER_DIR set:
xcrun simctl openurl booted "http://127.0.0.1:8799/index.html"
xcrun simctl io booted screenshot /tmp/shot.png
```

**Three real bugs came out of doing this, none visible on a desktop browser:**

- **No viewport meta.** Mobile Safari then lays out at its default 980px, the
  `min-width:900px` desktop breakpoint fires on a phone, and the rail sits beside
  the stage scaled to illegibility. The published Artifact hides this because the
  Artifact skeleton injects a viewport meta of its own; a real bundle serves this
  file directly and would have shipped broken.
- **`.thesis div` outranked `.narrow-hide`** (0,1,1 against 0,1,0), so the
  phone-only hide never applied and the stats sat on top of the title.
- **The rail is a flex column, and flex children shrink before a container
  overflows.** 1281px of controls compressed into a 386px rail: buttons 28px tall
  rendered at 14, every row squashed, `overflow-y:auto` never engaging. It looks
  exactly like clipping and is not. `#rail > *{flex:0 0 auto}` is the fix.

That last one survived two wrong guesses. **Measure before changing CSS**: append
a fixed overlay that prints `getBoundingClientRect()` for the suspect elements and
screenshot it in the simulator. `tools/` deliberately does not carry that script,
because it is a debugging move rather than part of the build — but write it with
an editor, never a bash heredoc, or the JS newline escapes become real newlines,
every string literal comes out unterminated, and the block dies silently. That
happened here too; see `dev/CLAUDE.md`, "Windows gotchas".

`vh` is *not* the culprit for the rail, though it was worth fixing anyway: iOS
resolves it against the largest viewport, the one with the URL bar hidden, so the
layout is taller than what you can see. `dvh` with a `100%` fallback, and a flex
percentage split rather than `44vh` + `52vh`.

## γ and α do not share a vertex, and drawing them as though they did was wrong

`conventions.md` §3 defines α as an azimuth and stops there, so the app drew its
arc at the apex, in the d̂–n̂ plane, terminating on the direction `(sin α, cos α,
0)`. The *measure* was right and the *anchor* was not, which is the worst
combination: nothing in the picture sat on that leg, so the figure read as the
angle between n̂ and k̂ᵢ, which is **90.6°, not 25°**; and at rim focus, the
one view that exists to read azimuths, it left the frame entirely.

The thesis is explicit where `conventions.md` is silent. `fig:grating_angles`
has **γ ≡ ∠AIC at the apex and α ≡ ∠ACB at C, the centre of the cone's base
circle**, and `grating-metapost/geometry/yaw.mp` draws it there too, with
`B--F` commented `% reference line for alpha`. So α now sits on the rim: vertex
on the cone axis, near leg to the −n̂ rim point, far leg to where the beam
pierces it. That is also the construction `fig:ALS_arc` **measures** it by:
`sin α = Δx_dir / r` off the fitted arc centre.

k̂ᵢ continued forward *is* the rim point at azimuth π + α, so the direct beam
needs no construction of its own; it is the incident ray drawn through. With
transmission shown it coincides with transmitted m = 0, which is the same
statement twice and right both times.

One erratum found on the way, worth knowing before trusting the caption over
the equations: Chapter 2's `fig:grating_angles` caption reads `η ≡ ∠CIB and
φ ≡ ∠AIB`, but `yaw.tex`'s derivation has them the other way round. The blue
triangle gives `sin i = AB/L`, so η = ∠AIB and yaw = ∠BIC. **The equations are
self-consistent; the two symbols in that caption are swapped.**

## The mount has two parameterisations and one state

`(γ, α)` is how the diffraction is written; `(η, φ)` is how a grating is placed.
`sin η = sin γ cos α`, `sin φ = tan α tan η`, and the inverse is exact:
`α = atan2(sin φ cos η, sin η)`, `γ = asin √(sin²η + sin²φ cos²η)`.

**η is the pitch stage angle and the substrate graze angle at once.** The 2020
paper's figure calls it pitch, the thesis calls it the graze angle relative to
the substrate, and it is one number, measured from the surface, as ζ is, not
from the normal. There is no third angle to add.

**Roll adds to α, and "roll changes nothing" was written here first and is
wrong.** The mistake came from reading only the thesis's measurement section,
where `eq:measure_alpha` takes α off the direct beam, which roll cannot move,
and `eq:measure_roll` then recovers ϕ from the 0-order offset. That is roll as a
frame misalignment. Operationally it is the other thing: roll turns the grating
about the groove axis, γ is the angle *to* that axis and cannot see it, so
**α = α(η, φ) + ϕ**. Dial η and φ against a mount that is not level and you land
somewhere other than the α your stage settings imply.

In the grating frame that makes roll degenerate with the α knob, which is why it
is offered only in the axes mount and only there. Note the collision with the
viewer's own two-finger roll: the state is `S.groll`, never `S.roll`.

It is also why **there are two ηs once ϕ ≠ 0** and the app shows both. The knob
is the stage pitch, set against the optic mount, and answers to the nominal α;
the header is the graze the surface actually sees, and answers to the real one.
They are equal at zero roll, which is every geometry anybody intends, and the
one that must be compared against a critical angle is the header's. `grazeAt()`
and `yawAt()` therefore take an explicit α rather than reading `S.alpha`.

**Three conditions are one: α = 0, φ = 0, η = γ.** `sin η = sin γ cos α`
collapses to `sin η = sin γ`, and `sin φ = tan α tan η` to zero. That is the
exact off-plane mount, and its γ = 90° end is **normal incidence**: k̂ᵢ = −n̂,
`sin β_m = mλ/p`, orders symmetric about the normal. It is also the singular
point of the axis map, where η = 90°, the beam has no projection in the surface,
and **every φ gives the same geometry**. So the yaw knob there is inert, and
reads `—` rather than `0.000°`, because a knob showing a number while doing
nothing looks broken instead of degenerate.

One presentational trap that came with it: γ printed at 2 places and η at 3 made
`η = γ` read as `1.50` against `1.496`, which is one number twice. Both go
through `fmtAng` now.

`(γ, α)` stays the single state and `(η, φ, ϕ)` is always derived, so the pairs
cannot drift. Two things about that were got wrong first and are easy to repeat:

- **Clamp in axis space, not after converting.** Clamping α afterwards looks
  equivalent and is not: it leaves γ where the yaw put it, and η is a function
  of both, so **η walked from 1.359° to 5.397° while its own knob was
  untouched.** Each cone limit is restated as an axis limit instead. α's ±80
  bounds yaw by `|sin φ| ≤ tan 80 tan η`, which at η = 1.36° is 7.7° and is the
  real statement that at grazing pitch a couple of degrees of yaw is the whole
  usable range.
- **γ's floor bounds η from below, and "floor η at γ's own 0.25" is wrong.**
  η ≤ γ always, so it looks sufficient; it instead deletes reachable geometry,
  because γ = 0.25° with α = 80° is η = 0.043°. A slider that could not hold it
  snapped the scene by **30° of α** the first time an axis knob was touched.
  Solving `sin²η + sin²φ cos²η = sin²γ_min` for η gives the floor that actually
  applies at the current yaw, and above |φ| = γ_min the yaw alone already holds
  γ up so there is none left to apply. Round-trip error over a 56-point grid is
  then ≤ 1.4°, and the only two cases past 1° are γ = 90° with α = ±80°, where
  (η, φ) = (10°, ±90°) sits on the domain boundary and the map is degenerate.
- **Roll is clamped last, against what is left of α's range**, for the same
  reason. Letting α take the clamp would put the nominal α somewhere other than
  `fromAxes()` left it, and η and φ would walk again. Measured with the clamp
  in: 140 roll settings across a (γ, α) grid, **zero drift** in η, φ or γ.

Both were found by driving the sliders from the console and reading the config
line back, which is the same move the gesture work needed and the only one that
catches a knob moving a readout it does not own.

Two smaller notes. Yaw is violently nonlinear near zero (at η = 1.36°, half a
degree of yaw moves α by 20°), so its knob uses γ's geometric mapping mirrored
about a small dead zone, because `geo()` bottoms out at its lower bound and a
yaw readout of 0.004° is a worse lie than a detent. And `.phys{display:flex}` is
(0,1,0) against the UA sheet's `[hidden]` at (0,0,1), so a hidden slider row
still lays out until `.phys[hidden]{display:none}` says otherwise: the same
clash as `.thesis div` against `.narrow-hide`.

## Transmission is a branch, not a second grating equation

`conventions.md` §4 is explicit: a transmitted order keeps the **same** equation
and the same `sin β_m`, and is distinguished only by `cos β_m < 0`. Some
literature rewrites transmission as `mλ/p = sin α − sin β_m` by redefining
`β_m → β_m − π`; the package refuses to, and so does this app.

Two things follow, and the app exists partly to show them:

- **The propagating set is branch-independent.** `|sin β_m| ≤ 1` never mentions
  the branch, so an order propagates in reflection and transmission together, or
  in neither.
- **Both branches lie on the same cone**, mirrored through the n̂ plane, because
  `β_T = π − β_R` flips only the `cos β` component of
  `k̂ = (sin γ sin β, sin γ cos β, cos γ)`.

`betaTransmitted()` returns the raw `π − β_R`, which is what the vectors want.
`betaTdeg()` wraps it into (−180°, 180°] **for display only** — a table reading
231.84° instead of −128.16° invites exactly the thought that transmission uses a
different equation.

**There is no transmitted efficiency here and there must not appear to be one.**
The ported solver is a reflection-grating model: its phase is the reflection
double pass, and `flux_obliquity` with `cos β_m < 0` returns a negative number
rather than an answer. Transmitted rays are therefore drawn **dashed and at
uniform width**, so ray thickness — which for the reflected branch *is* the
efficiency — cannot be misread, and the table shows `—` rather than a blank that
could pass for zero. A provenance item states it. The package's integral solver
does carry transmission (`_finite.py`, `R + T = 1`); porting that is the only
honest route to a number here.

## Three reflectivity models, and only one is reciprocal

`local` evaluates the complex Fresnel amplitude per quadrature point and carries
it **inside** the integral, weighted by `√r(ζ_in)·√r(ζ_out)`. `average` and
`facet` each produce **one factor per wavelength** applied outside it — so both
scale every order by the same number and stay order-independent, where `local`
does not.

The difference that matters is not resolution, it is symmetry. `average` resolves
the groove and still breaks reciprocity, because its `ζ(t)` is built from `α`
alone. Symmetrising in the exit direction is what repairs it, and only `local`
does that. Do not "improve" `average` by resolving it further; that is the
measurement the package already made.

Implementation notes that are easy to get wrong:

- `average` averages `R(ζ(t))` over the **whole period**, with shadowed points
  contributing zero — not over the lit part. Averaging only what is visible
  would quietly delete the shadowing the model exists to see.
- `facet`'s single angle is `arcsin(sin γ · cos(δ − α))`, exact for a Blazed
  profile because it has one flat active facet.
- **Only `local` has masks, so only `local` can suppress an order.** Pushing to
  `suppressed` from the other two would report geometry that was never computed.
- The bare `|G_m|²` is computed for every model, since `average` and `facet` are
  that value scaled. `local` is the extra pass, and it runs whenever the model is
  `local` **or** the caller asked for the comparison.

The app reports all three sums together with the other two as a percentage
difference from `local`. That is the point of having all three: the size of each
approximation becomes measurable rather than asserted. At the reference geometry
it is about −0.8% and −0.6%; on a shallow blaze, where almost nothing is
shadowed, `average` converges toward `facet`.

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

The package is checked out at its default branch rather than a pinned ref, for
the reason nanofab-simulator pins nothing on hologram. **Do not write `ref: main`
there.** Every magmacrunch repo uses `main`; the package uses **`master`**, and
that is the only place in this tree where the two accounts differ on it. Naming
the wrong branch fails at checkout with a bare `The process '/usr/bin/git' failed
with exit code 1`, which mentions neither the branch nor the repository — the
first CI run here died exactly that way. Omitting `ref:` takes whatever the
default is and survives a later rename.

CI also passes `$GRATINGLAB` rather than using the flat `../gratinglab` layout,
because with both repos called gratinglab that layout cannot exist — one would
have to sit inside the other.

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
