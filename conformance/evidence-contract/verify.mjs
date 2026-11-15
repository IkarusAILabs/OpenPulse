#!/usr/bin/env node
// Verify the content hash of OpenPulse evidence-contract 2.x documents.
//
// Standalone: Node 18+ and nothing else (no OpenPulse, no npm packages).
// Usage: node verify.mjs contracts.jsonl   (or a single .json document)
// Exit 0 when every document verifies, 1 otherwise.
//
// Only the 2.x versions OpenPulse has published are accepted (VERSIONS; a
// test keeps it equal to schemas/evidence-contract/), and the document's
// provenance.contract_version must be its top-level contract_version.
// 1.x documents use a different hash rule; validate them with the
// standalone consumer (conformance/consumer/).
//
// content_hash = "sha256:" + hex(SHA-256(JCS(body))), where body is the
// document without signature, signing_key_id and trust_root, and without
// provenance.content_hash and provenance.generation_timestamp.
// JCS is RFC 8785; in JavaScript it is JSON.stringify for primitives and
// members sorted by UTF-16 code units, which is Array.prototype.sort's
// default order.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

function jcs(value) {
  if (value === null || typeof value !== "object") {
    if (typeof value === "number" && !Number.isFinite(value)) {
      throw new Error("NaN and infinities have no JSON form");
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return "[" + value.map(jcs).join(",") + "]";
  }
  const keys = Object.keys(value).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + jcs(value[k])).join(",") + "}";
}

export function contentHash(doc) {
  const body = { ...doc };
  for (const k of ["signature", "signing_key_id", "trust_root"]) delete body[k];
  body.provenance = { ...doc.provenance };
  delete body.provenance.content_hash;
  delete body.provenance.generation_timestamp;
  return "sha256:" + createHash("sha256").update(jcs(body), "utf8").digest("hex");
}

export const VERSIONS = ["2.0.0", "2.1.0", "2.2.0", "2.3.0", "2.4.0"];

export function verify(doc) {
  if (!VERSIONS.includes(doc.contract_version)) {
    return `unsupported contract_version ${JSON.stringify(doc.contract_version)} (${VERSIONS.join(", ")})`;
  }
  if (doc.provenance?.contract_version !== doc.contract_version) {
    return "provenance.contract_version differs from contract_version";
  }
  if (doc.provenance?.content_hash_method !== "jcs-sha256") return "content_hash_method is not jcs-sha256";
  return contentHash(doc) === doc.provenance.content_hash ? null : "content_hash does not match";
}

const path = process.argv[2];
if (path) {
  const text = readFileSync(path, "utf8").trim();
  const docs = text.startsWith("[") || !text.includes("\n") ? [].concat(JSON.parse(text)) : text.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  let failed = 0;
  docs.forEach((doc, i) => {
    const problem = verify(doc);
    if (problem) failed += 1;
    console.log(`${i + 1}: ${problem ? "FAIL " + problem : "OK"} ${doc.provenance?.content_hash ?? ""}`);
  });
  process.exit(failed ? 1 : 0);
}
