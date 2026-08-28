#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-$HOME/Master-Repo-Use}"
MODE="all"
AUTO=0
for arg in "$@"; do
  case "$arg" in
    --copilot-only) MODE="--copilot-only" ;;
    --auto-skills)  AUTO=1 ;;
  esac
done
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
  python3 - "$file" "$BEGIN" "$END" "$body" <<'PY'
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

if [ "$MODE" != "--copilot-only" ]; then
  upsert_block "$HOME/.claude/CLAUDE.md" "$common
Claude-specific entrypoint: $REPO_PATH/CLAUDE.md"
  upsert_block "$HOME/.codex/AGENTS.md" "$common"
  mkdir -p "$HOME/.gemini"
  upsert_block "$HOME/.gemini/GEMINI.md" "$common
Gemini-specific entrypoint: $REPO_PATH/GEMINI.md"
fi

mkdir -p "$HOME/.copilot"
upsert_block "$HOME/.copilot/copilot-instructions.md" "$common
Copilot-specific guide: $REPO_PATH/docs/COPILOT-SETUP.md"

for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  touch "$rc"
  python3 - "$rc" "$REPO_PATH" <<'PY'
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
[ "$MODE" = "--copilot-only" ] || echo "Claude: $HOME/.claude/CLAUDE.md | Codex: $HOME/.codex/AGENTS.md | Gemini: $HOME/.gemini/GEMINI.md"
echo "Watermark command: master-watermark <input> <output-folder>"
echo "GitHub audit: gh workflow run catalog-guardian.yml -R Charlesganu2004/Master-Repo-Use"
echo "Optional AI request: python $REPO_PATH/scripts/maintenance_request.py --auto"
echo "Token budget remains opt-in: $REPO_PATH/docs/TOKEN-BUDGET.md"
[ "$AUTO" = "1" ] && echo "Auto mode written to every client instruction file." \n  || echo "Auto mode not enabled. Re-run with --auto-skills to turn it on."
