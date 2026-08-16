const ignoredRules = new Set([
  "slopless/coleman-liau",
  "slopless/flesch-kincaid",
  "slopless/gunning-fog",
  "slopless/automated-readability",
  "slopless/smog",
  "slopless/dale-chall",
  "slopless/sentence-length",
  "slopless/paragraph-length",
  "slopless/sentence-case",
]);

let raw = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) raw += chunk;

let reports;
try {
  reports = JSON.parse(raw || "[]");
} catch {
  console.error("slopless returned invalid JSON");
  process.exit(2);
}

let findings = 0;
for (const report of reports) {
  for (const message of report.messages ?? []) {
    if (ignoredRules.has(message.ruleId)) continue;
    if (message.ruleId === "slopless/prohibited-words" && /[\"']Unlock[\"']/.test(message.message)) continue;
    findings += 1;
    const file = (report.filePath ?? "unknown").split("/").pop();
    console.log(`  ${file}:${message.line} ${message.ruleId}: ${message.message}`);
  }
}

if (findings) {
  console.log(`slopless: FAIL (${findings} prose-pattern finding(s))`);
  process.exit(1);
}
console.log("slopless: OK (readability and length metrics excluded)");
