import assert from "node:assert/strict";
import { test } from "node:test";
import { isDevRoute } from "../../lib/client/dev-only.ts";

test("the UI gallery answers everywhere except in production", () => {
  assert.equal(isDevRoute("production"), false);
  assert.equal(isDevRoute("development"), true);
  assert.equal(isDevRoute("staging"), true);
  assert.equal(isDevRoute(undefined), true);
});
