#!/usr/bin/env node

/**
 * Generates a Markdown QA report from a JSON input of test results.
 * Usage: node generate_qa_report.cjs '<json_results>'
 */

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Error: No test results provided.");
  process.exit(1);
}

try {
  const results = JSON.parse(args[0]);
  let report = "# Hummingbot Connector QA Report\n\n";
  report += "| Test Case | Status | Notes |\n";
  report += "|-----------|--------|-------|\n";

  results.forEach(test => {
    const statusIcon = test.status === "PASS" ? "✅" : test.status === "SKIPPED" ? "⏭️" : "❌";
    report += `| ${test.name} | ${statusIcon} ${test.status} | ${test.notes || ""} |\n`;
  });

  console.log(report);
} catch (error) {
  console.error("Error parsing results JSON:", error.message);
  process.exit(1);
}
