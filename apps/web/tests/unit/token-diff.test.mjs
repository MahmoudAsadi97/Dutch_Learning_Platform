import assert from "node:assert/strict";
import { test } from "node:test";
import { diffParts, hasDifference } from "../../components/exercise/tokenParts.ts";

const same = (word) => ({ op: "same", expected: word, given: word });

test("matched words read as one stretch, and each change is its own part", () => {
  const ops = [
    same("ik"),
    same("leg"),
    { op: "changed", expected: "identiteitskaart", given: "identiteitskart" },
    same("klaar"),
    same("voor"),
    { op: "missing", expected: "mijn", given: "" },
    same("afspraak"),
    { op: "extra", expected: "", given: "nu" },
  ];
  assert.deepEqual(diffParts(ops), [
    { kind: "same", text: "ik leg" },
    { kind: "changed", given: "identiteitskart", expected: "identiteitskaart" },
    { kind: "same", text: "klaar voor" },
    { kind: "missing", expected: "mijn" },
    { kind: "same", text: "afspraak" },
    { kind: "extra", given: "nu" },
  ]);
  assert.equal(hasDifference(ops), true);
});

test("an answer typed exactly right has nothing to point at", () => {
  const ops = [same("het"), same("huis")];
  assert.deepEqual(diffParts(ops), [{ kind: "same", text: "het huis" }]);
  assert.equal(hasDifference(ops), false);
  assert.deepEqual(diffParts([]), []);
});
