import assert from "node:assert/strict";
import { test } from "node:test";
import { ALPHABET_REVIEW_STATUS, DUTCH_ALPHABET, DUTCH_LETTER_PAIRS, letterQuestion } from "../../lib/alphabet.ts";

test("the alphabet has 26 unique letters and explicit Dutch names, distinct from digraphs", () => {
  assert.equal(DUTCH_ALPHABET.map(item => item.letter).join(""), "ABCDEFGHIJKLMNOPQRSTUVWXYZ");
  assert.equal(DUTCH_ALPHABET.find(item => item.letter === "W").speech, "wee");
  assert.equal(DUTCH_ALPHABET.find(item => item.letter === "I").speech, "ie");
  assert.equal(DUTCH_ALPHABET.find(item => item.letter === "Y").speech, "ypsilon");
  assert.equal(DUTCH_ALPHABET.some(item => item.letter === "IJ"), false);
  assert.ok(DUTCH_LETTER_PAIRS.some(item => item.letters === "ij"));
  assert.equal(ALPHABET_REVIEW_STATUS, "unreviewed");
});

test("all alphabet and sound examples have Dutch, English and Persian text", () => {
  for (const item of [...DUTCH_ALPHABET, ...DUTCH_LETTER_PAIRS]) {
    for (const language of ["nl", "en", "fa"]) assert.ok(item.example[language].trim());
  }
});

test("the recognition round reaches every letter and never offers duplicate or missing options", () => {
  const seen = new Set();
  for (let round = 0; round < 26; round++) {
    const question = letterQuestion(round);
    seen.add(question.target.letter);
    assert.equal(new Set(question.options.map(item => item.letter)).size, 4);
    assert.ok(question.options.some(item => item.letter === question.target.letter));
  }
  assert.equal(seen.size, 26);
});
