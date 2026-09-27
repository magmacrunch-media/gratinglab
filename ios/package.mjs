#!/usr/bin/env node
/**
 * Build the App Store bundle from `app/`.
 *
 *     node ios/package.mjs        (or `npm run build` in ios/)
 *
 * Output is `ios/www/`, generated and gitignored, and Capacitor's webDir.
 * Never edit it; edit `app/` and rebuild.
 *
 * There is exactly one thing wrong with `app/index.html` in a bundle: it asks
 * Google for IBM Plex. That is right on a web page and wrong in an app that
 * claims to make no network connection of any kind, so this script vendors the
 * faces and rewrites the request into a local @font-face block. Everything else
 * about the page is already self-contained -- it reaches out of its own folder
 * for nothing, which is what the CI guard in .github/workflows/ci.yml keeps
 * true.
 *
 * The machinery is hypnopompia's shared pipeline, the one the arcade games and
 * crunchscope use. Its contract is kept here too: every edit must change
 * something or the build stops, and the final sweep refuses a bundle that
 * reaches outside itself or loads anything over the network.
 */

import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const IOS = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(IOS, '..');

// hypnopompia, found the way the games find it: $HYPNOPOMPIA, then the flat
// layout, then this tree. apps/ sits beside engines/ exactly as games/ does.
const SHELL = [
  process.env.HYPNOPOMPIA && resolve(process.env.HYPNOPOMPIA),
  resolve(REPO, '..', 'hypnopompia'),
  resolve(REPO, '..', '..', 'engines', 'hypnopompia'),
].filter(Boolean).find((r) => existsSync(join(r, 'pipeline', 'index.mjs')));

if (!SHELL) {
  console.error('\npackage.mjs: no hypnopompia checkout found.');
  console.error(
    'The shared bundle pipeline lives there. Looked for pipeline/index.mjs under\n'
    + '  $HYPNOPOMPIA, ../hypnopompia, ../../engines/hypnopompia\n'
    + 'Set HYPNOPOMPIA=<path to the hypnopompia checkout> to look elsewhere.'
  );
  process.exit(1);
}

const { createBuild, transforms } = await import(
  pathToFileURL(join(SHELL, 'pipeline', 'index.mjs')).href
);

// No `probe`: this page reads nothing from the website, so the pipeline never
// resolves a checkout of it. That is hypnopompia 8a73ddf, which made the lookup
// lazy for exactly this consumer.
const b = createBuild({ ios: IOS, web: 'app' });

/**
 * The faces app/index.html asks Google for, as @fontsource names them.
 *
 * Weights are the ones the page actually sets: Plex Sans at 400/500/600 and
 * Plex Mono at 400/500. Shipping the rest would be dead weight in a bundle
 * nobody can trim later.
 */
const FACES = [
  { pkg: '@fontsource/ibm-plex-sans', file: 'ibm-plex-sans-latin-400-normal.woff2', family: 'IBM Plex Sans', weight: 400 },
  { pkg: '@fontsource/ibm-plex-sans', file: 'ibm-plex-sans-latin-500-normal.woff2', family: 'IBM Plex Sans', weight: 500 },
  { pkg: '@fontsource/ibm-plex-sans', file: 'ibm-plex-sans-latin-600-normal.woff2', family: 'IBM Plex Sans', weight: 600 },
  { pkg: '@fontsource/ibm-plex-mono', file: 'ibm-plex-mono-latin-400-normal.woff2', family: 'IBM Plex Mono', weight: 400 },
  { pkg: '@fontsource/ibm-plex-mono', file: 'ibm-plex-mono-latin-500-normal.woff2', family: 'IBM Plex Mono', weight: 500 },
];

// 1. The page and its own files.
b.copyWeb();
const state = b.openPage();

// 2. The faces, from node_modules into the bundle.
mkdirSync(join(b.OUT, 'fonts'), { recursive: true });
for (const face of FACES) {
  const src = join(IOS, 'node_modules', ...face.pkg.split('/'), 'files', face.file);
  if (!existsSync(src)) {
    b.die(
      `${face.file} is missing.`,
      `It comes from the ${face.pkg} dev dependency: run \`npm install\` in ios/.`
    );
  }
  cpSync(src, join(b.OUT, 'fonts', face.file));
}
for (const pkg of ['@fontsource/ibm-plex-sans', '@fontsource/ibm-plex-mono']) {
  const lic = join(IOS, 'node_modules', ...pkg.split('/'), 'LICENSE');
  if (existsSync(lic)) {
    cpSync(lic, join(b.OUT, 'fonts', `${pkg.split('/')[1]}-LICENSE.txt`));
  }
}

const FACE_CSS = FACES.map((f) => `@font-face{font-family:"${f.family}";`
  + `font-style:normal;font-weight:${f.weight};font-display:swap;`
  + `src:url("fonts/${f.file}") format("woff2");}`).join('\n');

// 3. The page. One edit: the network request becomes the local faces.
//    The preconnect goes with it -- it is a hint to a host this bundle must
//    never contact, and leaving it would trip the self-contained sweep.
b.edit(state, 'vendor IBM Plex instead of fetching it from Google', (html) =>
  html.replace(
    /<link rel="preconnect"[^>]*>\s*<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/,
    `<style>\n${FACE_CSS}\n</style>`
  )
);

// 4. The title screen's publisher mark becomes plain text.
//
//    In a WKWebView an <a href="https://..."> with no target navigates the web
//    view itself, and there is no back: the application would simply become
//    magmacrunch.com. george-boole unwraps the same mark for the same reason,
//    and adds a second one worth keeping -- an outbound link on the FIRST
//    screen sends a tester to Safari before they have seen anything. The
//    credits carry the links instead, which is the next step.
b.edit(state, 'unwrap the publisher mark, which is a link only on the web', (html) =>
  html.replace(
    /<a class="title-publisher-link" href="[^"]*">([\s\S]*?)<\/a>/,
    '<span class="title-publisher-link">$1</span>'
  )
);

// 5. Every remaining outbound link opens in the system browser rather than in
//    place. After the step above these are all in credits, where a tester has
//    chosen to go looking.
transforms.outboundLinks(b, state);

b.writePage(state);

// 6. Nothing may reach outside the bundle or over the network.
b.sweepSelfContained();

console.log(`package.mjs: built ${b.OUT}`);
for (const step of state.applied) console.log(`  - ${step}`);
