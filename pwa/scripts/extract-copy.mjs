import { readFileSync } from "node:fs";
import ts from "typescript";

const sourcePath = new URL("../src/App.tsx", import.meta.url);
const source = readFileSync(sourcePath, "utf8");
const tree = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const copy = [];

function add(value) {
  const text = value.replace(/\s+/g, " ").trim();
  if (!text || !/[A-Za-z]/.test(text) || /^https?:\/\//.test(text)) return;
  copy.push(text);
}

function templateText(node) {
  if (ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (!ts.isTemplateExpression(node)) return "";
  return [node.head.text, ...node.templateSpans.map((span) => ` ${span.literal.text}`)].join("");
}

function insideJsxExpression(node) {
  for (let parent = node.parent; parent; parent = parent.parent) {
    if (ts.isJsxAttribute(parent)) return false;
    if (ts.isJsxExpression(parent)) return true;
    if (ts.isSourceFile(parent)) return false;
  }
  return false;
}

function visit(node) {
  if (ts.isJsxText(node)) add(node.text);

  if (ts.isJsxAttribute(node) && node.initializer && ts.isStringLiteral(node.initializer)) {
    const name = node.name.getText(tree);
    if (["alt", "aria-label", "placeholder", "title"].includes(name)) add(node.initializer.text);
  }

  if (ts.isPropertyAssignment(node)) {
    const name = node.name.getText(tree).replace(/["']/g, "");
    if (["summary", "title"].includes(name) && ts.isStringLiteralLike(node.initializer)) add(node.initializer.text);
  }

  if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && /^(useState|set[A-Z])/.test(node.expression.text)) {
    const first = node.arguments[0];
    if (first && ts.isStringLiteralLike(first)) add(first.text);
    if (first && ts.isTemplateExpression(first)) add(templateText(first));
  }

  if (insideJsxExpression(node)) {
    if (ts.isStringLiteral(node) && /\s/.test(node.text)) add(node.text);
    if (ts.isTemplateExpression(node)) add(templateText(node));
  }

  ts.forEachChild(node, visit);
}

visit(tree);

console.log("# PWA user-visible copy\n");
for (const text of [...new Set(copy)]) console.log(`${text}\n`);
