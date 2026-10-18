import assert from "node:assert/strict";
import { test } from "node:test";
import { destinations, navItemFor, navSection, rooms } from "../../components/shell/nav.ts";

test("one learning entrance, dashboard and two account destinations", () => {
  assert.deepEqual(
    destinations.map((item) => item.href),
    ["/", "/leerpad"],
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
    "/verhalen": "/leerpad",
    "/verhalen/abc": "/leerpad",
    "/videos": "/leerpad",
    "/videos/xyz": "/leerpad",
    "/spreken": "/leerpad",
    "/missions": "/leerpad",
    "/missions/appointment-change": "/leerpad",
    "/speech-check": "/leerpad",
    "/woorden": "/leerpad",
    "/oefenen": "/leerpad",
    "/progress": "/progress",
    "/settings": "/settings",
    "/settings?tab=x": "/settings",
    "/over": "/settings",
  };
  for (const [path, section] of Object.entries(expected)) {
    assert.equal(navSection(path), section, path);
  }
  assert.equal(navSection("/dev/ui"), null);
  assert.equal(navSection("/unknown"), null);
});

test("headers keep every learning route within Leren", () => {
  assert.equal(navItemFor("/dev/ui").href, "/");
  assert.equal(navItemFor("/missions/x").label, "Leren");
  assert.equal(navItemFor("/leerpad").label, "Leren");
  assert.equal(navItemFor("/learn/pre-a2?section=stories").label, "Leren");
  assert.equal(navItemFor("/settings").accent, "neutral");
});

test("each navigation label is the Dutch of its copy entry, so the sidebar and the tabs say the same", async () => {
  const { uiCopy } = await import("../../lib/ui-copy.ts");
  for (const item of [...destinations, ...rooms]) {
    assert.equal(uiCopy.nav[item.copy]?.nl, item.label, item.href);
  }
});
