import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import ts from "typescript";

/**
 * Interface text written straight into components instead of coming from the catalogue, found with the
 * TypeScript parser: JSX text; strings and template text a JSX expression renders (`{busy ? "Bezig…" :
 * "Start"}`); string values of the attributes a learner reads or hears (aria-label, placeholder, title, alt,
 * label, description); and inline `nl:` strings, the shape of a trilingual label that bypasses the
 * catalogue and its Persian review. Shared by the ratchet test and the budget recount.
 */
export const web = path.resolve(import.meta.dirname, "..", "..");

const SPOKEN_ATTRIBUTES = new Set(["aria-label", "placeholder", "title", "alt", "label", "description"]);
const WORDS = /\p{L}{2,}/u;

/** Strings an expression shows as text: itself, both branches of a condition, the right side of && / || / ??. */
function shownStrings(node, out) {
  if (!node) return;
  if (ts.isParenthesizedExpression(node) || ts.isAsExpression(node))
    return shownStrings(node.expression, out);
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return void out.push(node.text);
  if (ts.isTemplateExpression(node)) {
    out.push([node.head.text, ...node.templateSpans.map((span) => span.literal.text)].join(" "));
    return;
  }
  if (ts.isConditionalExpression(node)) {
    shownStrings(node.whenTrue, out);
    shownStrings(node.whenFalse, out);
    return;
  }
  if (ts.isBinaryExpression(node)) {
    const kind = node.operatorToken.kind;
    if (kind === ts.SyntaxKind.AmpersandAmpersandToken) return shownStrings(node.right, out);
    if (kind === ts.SyntaxKind.BarBarToken || kind === ts.SyntaxKind.QuestionQuestionToken) {
      shownStrings(node.left, out);
      shownStrings(node.right, out);
    }
  }
}

const isChild = (node) => node.parent && (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent));

export function hardCodedText(code, fileName = "component.tsx") {
  const source = ts.createSourceFile(fileName, code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const found = [];
  const visit = (node) => {
    if (ts.isJsxText(node)) {
      const text = node.text.replace(/\s+/g, " ").trim();
      if (text) found.push(text);
    } else if (ts.isJsxExpression(node) && isChild(node)) {
      shownStrings(node.expression, found);
    } else if (
      ts.isJsxAttribute(node) &&
      node.initializer &&
      SPOKEN_ATTRIBUTES.has(node.name.getText(source))
    ) {
      if (ts.isStringLiteral(node.initializer)) found.push(node.initializer.text);
      else if (ts.isJsxExpression(node.initializer)) shownStrings(node.initializer.expression, found);
    } else if (ts.isPropertyAssignment(node) && node.name.getText(source) === "nl") {
      shownStrings(node.initializer, found);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return found.filter((text) => WORDS.test(text));
}

export function sourceFiles(dir = "components", out = []) {
  for (const entry of readdirSync(path.join(web, dir), { withFileTypes: true })) {
    const rel = `${dir}/${entry.name}`;
    if (entry.isDirectory()) sourceFiles(rel, out);
    else if (entry.name.endsWith(".tsx")) out.push(rel);
  }
  return out;
}

export function measureAll() {
  const counts = {};
  for (const file of [...sourceFiles("components"), ...sourceFiles("app")].sort()) {
    const n = hardCodedText(readFileSync(path.join(web, file), "utf8"), file).length;
    if (n) counts[file] = n;
  }
  return counts;
}
