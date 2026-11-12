// Copies ~/.copilot/copilot-instructions.md verbatim into each cavecrew agent
// file. Copilot CLI does not pass custom instructions to subagents, and its
// subagents cannot read the file themselves (no shell, and the token-goat hook
// blocks large markdown reads), so the rules travel inside the agent prompt.
// Runs as a sessionStart hook. Prints nothing: hook output can enter context.
import { appendFileSync, readFileSync, readdirSync, writeFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const BEGIN = "<!-- global-rules-begin -->";
const END = "<!-- global-rules-end -->";
const MAX_PROMPT_CHARS = 30000;
const OLD_LINE = /^Global rules: this agent does not inherit[^\n]*\n(?:\n- `token-goat section [^\n]*\n)*/m;

const copilotHome = join(homedir(), ".copilot");
const agentsDir = join(copilotHome, "agents");
const logFile = join(copilotHome, "hooks", "cavecrew-rules-sync.log");
const log = (msg) => appendFileSync(logFile, `${new Date().toISOString()} ${msg}\n`);

try {
  const rules = readFileSync(join(copilotHome, "copilot-instructions.md"), "utf8").replace(/\r\n/g, "\n").trim();
  const block =
    `${BEGIN}\n` +
    "Global rules, copied word for word from ~/.copilot/copilot-instructions.md by the cavecrew-rules-sync hook. " +
    "Copilot CLI does not pass that file to subagents, so these are your rules. Never restate them in output.\n\n" +
    `${rules}\n${END}`;

  for (const name of readdirSync(agentsDir).filter((f) => /^cavecrew-.*\.md$/.test(f))) {
    const path = join(agentsDir, name);
    const original = readFileSync(path, "utf8").replace(/\r\n/g, "\n");
    const frontmatter = original.match(/^---\n[\s\S]*?\n---\n/);
    if (!frontmatter) {
      log(`skip ${name}: no frontmatter`);
      continue;
    }

    let body = original.slice(frontmatter[0].length).replace(OLD_LINE, "");
    const start = body.indexOf(BEGIN);
    const end = body.indexOf(END);
    if (start >= 0 && end > start) body = body.slice(0, start) + body.slice(end + END.length);
    body = body.replace(/^\n+/, "");

    const next = `${frontmatter[0]}\n${block}\n\n${body}`;
    const promptChars = next.length - frontmatter[0].length;
    if (promptChars > MAX_PROMPT_CHARS) {
      log(`skip ${name}: ${promptChars} chars exceeds the ${MAX_PROMPT_CHARS} agent prompt limit`);
      continue;
    }
    if (next !== original) writeFileSync(path, next, "utf8");
  }
} catch (err) {
  log(`error: ${err?.message ?? err}`);
}
