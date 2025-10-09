import fs from "fs";
import path from "path";
import yaml from "yaml";

const CONTRACT_RULES = path.resolve(__dirname, "../../enforcement/contract_rules.yml");

function buildSystemPrompt(rulesText) {
  return [
    "[ZERO-TOLERANCE CONTRACT — STRICT RULES]",
    "Always obey the contract. Return deterministic JSON patches only.",
    "---- CONTRACT YAML ----",
    rulesText,
    "------------------------"
  ].join("\n");
}

export async function runPreRequest() {
  if (!fs.existsSync(CONTRACT_RULES)) {
    console.warn("ZeroTolerance: contract_rules.yml is missing.");
    return { systemAppend: "" };
  }

  const raw = fs.readFileSync(CONTRACT_RULES, "utf8");
  try {
    yaml.parse(raw); // sanity check
  } catch (error) {
    console.error("ZeroTolerance: contract_rules.yml is invalid YAML.", error);
    return { systemAppend: "" };
  }

  console.log("ZeroTolerance: contract rules attached to system prompt.");
  return {
    systemAppend: buildSystemPrompt(raw)
  };
}
