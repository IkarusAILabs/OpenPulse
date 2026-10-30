'use strict';
// Bridge to node-semver for evaluation baseline V (evaluation/comparators/README.md).
// One JSON request per line on stdin, one JSON response per line on stdout.
//   {"id": 1, "op": "version"}            -> {"id": 1, "library": "semver", "version": "7.8.5"}
//   {"id": 2, "op": "parse", "v": "..."}  -> {"id": 2, "valid": true, "core": [1, 2, 3], ...}
//   {"id": 3, "op": "compare", "a", "b"}  -> {"id": 3, "cmp": -1 | 0 | 1 | null}
// Strict parsing only: no `loose`, no `coerce` (coerce invents versions).

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const semver = require('semver');

const pkg = JSON.parse(
  fs.readFileSync(path.join(path.dirname(require.resolve('semver')), 'package.json'), 'utf8'),
);

function parse(v) {
  const p = typeof v === 'string' ? semver.parse(v, { loose: false }) : null;
  if (!p) return { valid: false };
  return {
    valid: true,
    core: [p.major, p.minor, p.patch],
    prerelease: p.prerelease.length > 0,
    canonical: p.version,
  };
}

function handle(req) {
  switch (req.op) {
    case 'version':
      return { library: 'semver', version: pkg.version };
    case 'parse':
      return parse(req.v);
    case 'compare': {
      const a = parse(req.a);
      const b = parse(req.b);
      return { cmp: a.valid && b.valid ? semver.compare(req.a, req.b) : null };
    }
    default:
      return { error: `unknown op ${req.op}` };
  }
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', (line) => {
  let req;
  try {
    req = JSON.parse(line);
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: 'bad request' }) + '\n');
    return;
  }
  process.stdout.write(JSON.stringify({ id: req.id, ...handle(req) }) + '\n');
});
