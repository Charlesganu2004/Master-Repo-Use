#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-$HOME/Master-Repo-Use}"
# Which client instruction files to write. "all" is the default because a rule
# that lives in only one client is a rule the other clients will contradict.
CLIENT="all"
AUTO=1
prev=""
for arg in "$@"; do
  case "$prev" in
    --client)
      case "$arg" in
        all|claude|codex|gemini|copilot|antigravity|cursor) CLIENT="$arg" ;;
        gpt|chatgpt|openai) CLIENT="codex" ;;   # Codex is the GPT surface
        ag|google-antigravity) CLIENT="antigravity" ;;
        *) echo "Unknown --client '$arg'. Use all|claude|codex|gemini|copilot|antigravity|cursor." >&2; exit 2 ;;
      esac ;;
  esac
  case "$arg" in
    --copilot-only) CLIENT="copilot" ;;
    --auto-skills)  AUTO=1 ;;
  esac
  prev="$arg"
done

writes() { [ "$CLIENT" = "all" ] || [ "$CLIENT" = "$1" ]; }
# python3 on POSIX, plain python on Git Bash for Windows. Resolved once so a
# missing interpreter fails here with a clear message, not mid-write.
PY_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PY_BIN" ]; then
  echo "No python interpreter found on PATH (tried python3, python)." >&2
  exit 1
fi

BEGIN='<!-- MASTER-REPO-USE:BEGIN -->'
END='<!-- MASTER-REPO-USE:END -->'

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "Master Repo not found at $REPO_PATH" >&2
  exit 1
fi

upsert_block() {
  local file="$1"
  local body="$2"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  "$PY_BIN" - "$file" "$BEGIN" "$END" "$body" <<'PY'
import pathlib, sys
p=pathlib.Path(sys.argv[1]); begin=sys.argv[2]; end=sys.argv[3]; body=sys.argv[4]
text=p.read_text(encoding='utf-8') if p.exists() else ''
block=f"{begin}\n{body.rstrip()}\n{end}"
if begin in text and end in text:
    a=text.index(begin); b=text.index(end,a)+len(end)
    text=text[:a].rstrip()+"\n\n"+block+"\n"+text[b:].lstrip()
else:
    text=text.rstrip()+("\n\n" if text.strip() else "")+block+"\n"
p.write_text(text,encoding='utf-8')
PY
}

common="Master Repo path: $REPO_PATH
Use $REPO_PATH/AGENTS.md as the canonical portable contract. For tasks that may benefit from an agent framework, RAG, memory, MCP, observability, security, cloud/cost, quantum, Copilot, or another cataloged tool, search the Master Repo first and load only the relevant lane. Do not load the entire catalog into context. Follow its vetting, health, and security gates before installing or executing third-party code.
Routine maintenance is GitHub-first: use the repository Catalog Guardian and [Catalog Audit] owner-approval issue rather than scheduling model calls. Only Charles may approve deterministic maintenance with 'APPROVE CATALOG MAINTENANCE'. Use 'python $REPO_PATH/scripts/maintenance_request.py --auto' only when a maintenance task genuinely needs model judgment, and do not perform that work until Charles states 'APPROVE AI MAINTENANCE'. Never merge main without Charles approval."

AUTO_FILE="$REPO_PATH/docs/auto-mode-block.txt"
if [ "$AUTO" = "1" ]; then
  if [ ! -f "$AUTO_FILE" ]; then
    echo "Auto mode block not found at $AUTO_FILE" >&2
    exit 1
  fi
  common="$common
$(cat "$AUTO_FILE")"
fi

if writes claude; then
  mkdir -p "$HOME/.claude"
  upsert_block "$HOME/.claude/CLAUDE.md" "$common
Claude-specific entrypoint: $REPO_PATH/CLAUDE.md"
fi

if writes codex; then
  mkdir -p "$HOME/.codex"
  upsert_block "$HOME/.codex/AGENTS.md" "$common"
fi

# One file, two clients. Verified 2026-09-04 against
# antigravity.google/docs/rules-workflows/: Antigravity reads its GLOBAL rules
# from ~/.gemini/GEMINI.md, the same path the Gemini CLI uses, and not from any
# ~/.antigravity/ tree. So the block is written once for whichever of the two was
# asked for. Writing it twice would not double anything, but it would let the
# second body silently replace the first, which is worse.
if writes gemini || writes antigravity; then
  mkdir -p "$HOME/.gemini"
  upsert_block "$HOME/.gemini/GEMINI.md" "$common
Gemini-specific entrypoint: $REPO_PATH/GEMINI.md
Google Antigravity reads this same file as its global rules. Its skills live in ~/.gemini/config/skills/, its plugins in ~/.gemini/config/plugins/, and its MCP servers in ~/.gemini/config/mcp_config.json."
fi

# The part that is genuinely Antigravity-only. Its documented global skill path is
# ~/.gemini/config/skills/<folder>/SKILL.md, which the Gemini CLI does not read.
# Every skill in this repository already carries the one frontmatter field
# Antigravity requires, description, so they install as-is with no rewriting.
if writes antigravity; then
  "$PY_BIN" - "$REPO_PATH" "$HOME/.gemini/config/skills" <<'PY'
import pathlib, shutil, sys
source = pathlib.Path(sys.argv[1]) / "skills"
target = pathlib.Path(sys.argv[2])
target.mkdir(parents=True, exist_ok=True)
installed = []
for skill in sorted(p for p in source.iterdir() if p.is_dir()):
    if not (skill / "SKILL.md").is_file():
        continue                      # a directory without SKILL.md is not a skill
    destination = target / skill.name
    # Merge in place. Refreshing one managed skill must not delete files another
    # client or the owner deliberately placed in that capability directory.
    shutil.copytree(skill, destination, dirs_exist_ok=True)
    installed.append(skill.name)
print("Antigravity skills merged without deleting existing files: "
      + (", ".join(installed) or "none found"))
PY
fi

if writes copilot; then
  mkdir -p "$HOME/.copilot"
  upsert_block "$HOME/.copilot/copilot-instructions.md" "$common
Copilot-specific guide: $REPO_PATH/docs/COPILOT-SETUP.md"
fi

# Auto mode includes skills and supported hooks, even for a per-client command.
"$PY_BIN" "$REPO_PATH/scripts/install_auto_mode.py" --repo "$REPO_PATH" --home "$HOME" --client "$CLIENT"

for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  touch "$rc"
  "$PY_BIN" - "$rc" "$REPO_PATH" <<'PY'
import pathlib, sys, re
p=pathlib.Path(sys.argv[1]); repo=sys.argv[2]
text=p.read_text(encoding='utf-8') if p.exists() else ''
line=f'export COPILOT_CUSTOM_INSTRUCTIONS_DIRS="{repo}"'
pat=r'^export COPILOT_CUSTOM_INSTRUCTIONS_DIRS=.*$'
if re.search(pat,text,flags=re.M): text=re.sub(pat,line,text,flags=re.M)
else: text=text.rstrip()+"\n"+line+"\n"
p.write_text(text,encoding='utf-8')
PY
done
export COPILOT_CUSTOM_INSTRUCTIONS_DIRS="$REPO_PATH"

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/master-watermark" <<'WRAP'
#!/usr/bin/env bash
set -euo pipefail
TOOL="$HOME/.master-repo-tools/WatermarkRemover-AI"
echo "Use only on media you own or are authorized to modify."
if [ ! -d "$TOOL/.git" ]; then
  mkdir -p "$(dirname "$TOOL")"
  git clone https://github.com/D-Ogi/WatermarkRemover-AI.git "$TOOL"
  cd "$TOOL"
  chmod +x setup.sh
  ./setup.sh
else
  git -C "$TOOL" pull --ff-only || true
fi
cd "$TOOL"
exec python remwm.py "$@"
WRAP
chmod +x "$HOME/.local/bin/master-watermark"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

echo "Master Repo global AI setup complete."
echo "Repo: $REPO_PATH"
echo "Copilot instructions: $HOME/.copilot/copilot-instructions.md"
[ "$CLIENT" = "copilot" ] || echo "Claude: $HOME/.claude/CLAUDE.md | Codex: $HOME/.codex/AGENTS.md | Gemini and Antigravity: $HOME/.gemini/GEMINI.md"
echo "Watermark command: master-watermark <input> <output-folder>"
echo "GitHub audit: gh workflow run catalog-guardian.yml -R Charlesganu2004/Master-Repo-Use"
echo "Optional AI request: python $REPO_PATH/scripts/maintenance_request.py --auto"
echo "Token budget remains opt-in: $REPO_PATH/docs/TOKEN-BUDGET.md"
echo "Auto mode, discoverable skills and supported hooks installed for the selected client(s)."
