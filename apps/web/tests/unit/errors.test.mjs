import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { errorFor } from "../../lib/client/errors.ts";
import { uiCopy } from "../../lib/ui-copy.ts";

const copies = uiCopy.errors;
const api = (status, code = "") => ({ name: "Error", status, code });

test("the API's code decides before the status", () => {
  assert.equal(errorFor(api(429, "usage_limit"), copies), copies.limit);
  assert.equal(errorFor(api(503, "provider_unavailable"), copies), copies.modelAway);
  assert.equal(errorFor(api(503, "provider_failed"), copies), copies.modelAway);
  // a usage limit reported with another status still reads as the limit
  assert.equal(errorFor(api(409, "usage_limit"), copies), copies.limit);
});

test("without a known code the status decides", () => {
  assert.equal(errorFor(api(401), copies), copies.session);
  assert.equal(errorFor(api(403, "curriculum"), copies), copies.forbidden);
  assert.equal(errorFor(api(404, "story"), copies), copies.notFound);
  assert.equal(errorFor(api(413), copies), copies.tooLarge);
  assert.equal(errorFor(api(422), copies), copies.invalid);
  assert.equal(errorFor(api(429), copies), copies.limit);
  // a 502 from the API itself is a failed provider call: the screen words it, not "the server is away"
  assert.equal(errorFor(api(502), copies), copies.generic);
  assert.equal(errorFor(api(502, "api_unreachable"), copies), copies.serverAway);
  assert.equal(errorFor(api(504, "upstream_timeout"), copies), copies.serverAway);
  assert.equal(errorFor(api(503), copies), copies.modelAway);
  assert.equal(errorFor(api(500, "domain_error"), copies), copies.generic);
});

test("a dropped connection and anything unknown get honest general copy", () => {
  assert.equal(errorFor(new TypeError("Failed to fetch"), copies), copies.offline);
  assert.equal(errorFor(new Error("boom"), copies), copies.generic);
  assert.equal(errorFor(undefined, copies), copies.generic);
});

test("a screen can say something more precise for a code or a status", () => {
  const overrides = { 403: copies.checkLocked, story: copies.notFound };
  assert.equal(errorFor(api(403, "curriculum"), copies, overrides), copies.checkLocked);
  assert.equal(errorFor(api(400, "story"), copies, overrides), copies.notFound);
});

test("only a screen that keeps the input says it stays", () => {
  const keeps = { keepsInput: true };
  assert.equal(errorFor(new TypeError("Failed to fetch"), copies, {}, keeps), copies.offlineKept);
  assert.equal(errorFor(api(503), copies, {}, keeps), copies.modelAwayKept);
  assert.equal(errorFor(api(500), copies, {}, keeps), copies.genericKept);
  assert.equal(errorFor(api(429, "usage_limit"), copies, {}, keeps), copies.limitKept);
  assert.equal(errorFor(api(401), copies, {}, keeps), copies.session);
  for (const key of ["generic", "offline", "serverAway", "limit", "modelAway"]) {
    assert.doesNotMatch(copies[key].nl, /invoer|bewaard/, `${key} makes no claim about the input`);
    assert.match(copies[`${key}Kept`].nl, /Je invoer blijft staan/, `${key}Kept says the input stays`);
  }
});

test("a conflict reads by its code, never by the API's English sentence", () => {
  assert.equal(errorFor(api(409, "episodes_busy"), copies), copies.episodesBusy);
  assert.equal(errorFor(api(409, "videos_busy"), copies), copies.videosBusy);
  assert.equal(errorFor(api(409, "not_ready"), copies), copies.notReady);
  assert.equal(errorFor(api(409, "session_closed"), copies), copies.sessionClosed);
  assert.equal(errorFor(api(409, "in_progress"), copies), copies.inProgress);
  assert.equal(errorFor(api(409, "story"), copies), copies.generic);
  // an inherited property name is not a code
  assert.equal(errorFor(api(409, "constructor"), copies), copies.generic);
  assert.equal(errorFor(api(409, "toString"), copies, {}), copies.generic);
});

/** Codes whose message depends on the status or the screen: family codes, and one a screen words itself. */
const GENERAL_CODES = new Set([
  "domain_error",
  "curriculum",
  "practice",
  "audio",
  "vocabulary",
  "story",
  "video",
  "paid_not_approved",
]);

test("every error code the API sends has copy, or is listed as general on purpose", () => {
  const sent = new Set();
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".py"))
        for (const m of readFileSync(full, "utf8").matchAll(
          /(?<!\w)code(?:: str)? ?= ?"([a-z_]+)"|"code": "([a-z_]+)"/g,
        ))
          sent.add(m[1] ?? m[2]);
    }
  };
  walk(path.resolve(import.meta.dirname, "..", "..", "..", "api", "src"));
  assert.ok(sent.has("episodes_busy") && sent.has("usage_limit"), "the scan reads the API source");
  const unworded = [...sent].filter(
    (code) => !GENERAL_CODES.has(code) && errorFor(api(400, code), copies) === copies.generic,
  );
  assert.deepEqual(unworded, [], "give these codes catalogue copy in errorFor, or list them as general");
});

test("a failed episode or video says why, by its failure code", async () => {
  const { episodeFailure, videoFailure } = await import("../../lib/client/failures.ts");
  const failures = uiCopy.failures;
  assert.equal(episodeFailure("allowance", failures, false).body, failures.episodeAllowance);
  assert.equal(episodeFailure("quality", failures, false).title, failures.episodeQualityTitle);
  assert.equal(episodeFailure("paid_not_approved", failures, false).body, failures.paidNotApproved);
  assert.equal(episodeFailure("interrupted", failures, false).body, failures.writerAway);
  assert.equal(episodeFailure("interrupted", failures, true).body, failures.writerAwayDeveloper);
  assert.equal(videoFailure("allowance_video", failures), failures.videoTime);
  assert.equal(videoFailure("render_timeout", failures), failures.videoRender);
  assert.equal(videoFailure("too_long", failures), failures.videoTooLong);
  assert.equal(videoFailure(null, failures), failures.videoAway);
});
