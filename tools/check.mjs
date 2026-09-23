// Hold the JavaScript port to gratinglab's own ScalarSolver.
//
// The physics is extracted verbatim out of app/index.html, so this checks the
// code that actually ships rather than a copy of it that could drift. The
// reference values come from fixture.json, which is committed -- so this runs
// with node alone, and needs neither Python nor a gratinglab checkout.
//
//   node tools/check.mjs          exits 0 on agreement, 1 on drift
//
// Regenerate fixture.json with tools/ref.py when the solver changes.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const PAGE = join(HERE, "..", "app", "index.html");
const FIXTURE = join(HERE, "fixture.json");

// Agreement to 1e-9 relative. The port is the same arithmetic in the same
// order, so anything above float noise is a real difference: the first coated
// run failed at 1.8e-6 because the embedded Au table had been rounded to six
// significant figures, which is invisible in the app and wrong in every number.
const TOL = 1e-9;

const START = "  function sinBeta(";
const END = "  function scene(){";

const html = readFileSync(PAGE, "utf8");
const a = html.indexOf(START), b = html.indexOf(END);
if (a < 0 || b < 0) {
  console.error(`could not locate the physics block in ${PAGE}`);
  console.error(`expected a line starting "${START}" and one "${END}"`);
  process.exit(1);
}

const RAD = Math.PI / 180, DEG = 180 / Math.PI, MAX_DRAWN = 81;
const S = { period: 315.15, alpha: 25, gamma: 1.5, lambda: 3, blaze: 29.5, coating: false };

const make = new Function("S", "RAD", "DEG", "MAX_DRAWN",
  html.slice(a, b) +
  "\nreturn {sinBeta, propagating, orderRange, heightNm, scalarEfficiency, auAt};");
const F = make(S, RAD, DEG, MAX_DRAWN);

const ref = JSON.parse(readFileSync(FIXTURE, "utf8"));

let worst = 0, worstWhere = "", compared = 0, missing = 0;
for (const entry of ref) {
  const c = entry.case;
  S.period = c.period; S.alpha = c.alpha; S.gamma = c.gamma;
  S.lambda = c.lam; S.blaze = c.blaze; S.coating = !!c.coat;

  const [lo, hi] = F.orderRange();
  const marks = [];
  for (let m = lo; m <= hi; m++) {
    const s = F.sinBeta(m), p = F.propagating(s);
    marks.push({ m, s, beta: p ? Math.asin(s) : null, prop: p });
  }
  F.scalarEfficiency(marks);
  const byM = new Map(marks.map(k => [k.m, k.eff]));

  let sum = 0;
  for (const row of entry.orders) {
    if (!byM.has(row.m)) { missing++; continue; }
    const mine = byM.get(row.m);
    sum += mine;
    // relative where the value is meaningful, absolute where it is tiny
    const err = Math.abs(mine - row.E) / Math.max(row.E, 1e-6);
    compared++;
    if (err > worst) {
      worst = err;
      worstWhere = `${c.coat ? "Au" : "bare"} p=${c.period} g=${c.gamma} lam=${c.lam} m=${row.m}`;
    }
  }
  const sumErr = Math.abs(sum - entry.sum) / Math.max(entry.sum, 1e-30);
  console.log(
    `${c.coat ? "Au  " : "bare"} p=${String(c.period).padStart(7)} ` +
    `a=${String(c.alpha).padStart(5)} g=${String(c.gamma).padStart(5)} ` +
    `lam=${String(c.lam).padStart(5)} d=${String(c.blaze).padStart(5)}` +
    `  orders ${String(entry.orders.length).padStart(3)}` +
    `  sum ${sum.toExponential(6)}  rel ${sumErr.toExponential(2)}`
  );
}

console.log(`\n${compared} orders compared across ${ref.length} geometries` +
            (missing ? `, ${missing} MISSING from the port's order range` : ""));
console.log(`worst relative error: ${worst.toExponential(3)}` +
            (worstWhere ? `  (${worstWhere})` : ""));

if (!compared) {
  console.error("nothing was compared -- the fixture is empty or unreadable");
  process.exit(1);
}
if (missing || worst >= TOL) {
  console.error(`FAIL: tolerance is ${TOL.toExponential(0)}`);
  process.exit(1);
}
console.log("PASS");
