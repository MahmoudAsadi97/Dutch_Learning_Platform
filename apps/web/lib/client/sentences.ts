/** Keep the original text intact: decimal times and numbers must never be split into different facts. */
export function dutchSentences(text: string): string[] {
  if (!text) return [];
  if (typeof Intl.Segmenter !== "function") return [text];
  return Array.from(new Intl.Segmenter("nl-BE", { granularity: "sentence" }).segment(text), item => item.segment);
}
