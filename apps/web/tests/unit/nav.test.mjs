import assert from "node:assert/strict";
import { test } from "node:test";
import { destinations, navItemFor, navSection, rooms } from "../../components/shell/nav.ts";

test("five destinations and two rooms, every one with an accent and an icon", () => {
  assert.deepEqual(
    destinations.map((item) => item.href),
    ["/", "/leerpad", "/verhalen", "/spreken", "/woorden"],
  );
  assert.deepEqual(
    rooms.map((item) => item.href),
    ["/progress", "/settings"],
  );
  for (const item of [...destinations, ...rooms]) {
    assert.ok(item.label && item.short && item.icon && item.accent, item.href);
  }
});

test("every route belongs to one destination or room", () => {
  const expected = {
    "/": "/",
    "/leerpad": "/leerpad",
    "/learn/a1": "/leerpad",
    "/learn/a1/test": "/leerpad",
    "/verhalen": "/verhalen",
    "/verhalen/abc": "/verhalen",
    "/videos": "/verhalen",
    "/videos/xyz": "/verhalen",
    "/spreken": "/spreken",
    "/missions": "/spreken",
    "/missions/appointment-change": "/spreken",
    "/speech-check": "/spreken",
    "/woorden": "/woorden",
    "/progress": "/progress",
    "/settings": "/settings",
    "/settings?tab=x": "/settings",
  };
  for (const [path, section] of Object.entries(expected)) {
    assert.equal(navSection(path), section, path);
  }
  assert.equal(navSection("/dev/ui"), null);
  assert.equal(navSection("/unknown"), null);
});

test("an unknown path falls back to Vandaag for the header", () => {
  assert.equal(navItemFor("/dev/ui").href, "/");
  assert.equal(navItemFor("/missions/x").label, "Spreken");
  assert.equal(navItemFor("/settings").accent, "neutral");
});
