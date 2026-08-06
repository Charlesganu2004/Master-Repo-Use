# Portable Usage

These skills are plain Markdown with a small YAML header. Nothing in them is vendor-specific,
so the same file works as a Claude Code skill, an OpenAI developer message, or a system-prompt
prefix for a local model.

## File shape

```markdown
---
name: cite-or-abstain
description: Use when producing factual claims that a reader will act on...
---

# Cite or Abstain
...body...
```

Two header fields do the work:

- `name` — the identifier
- `description` — **the routing signal.** It states *when to use this*, not what it is. This
  is what a model reads to decide whether to load the body. A description that says
  "About citations" routes badly; one that says "Use when producing factual claims that a
  reader will act on" routes well.

Everything below the header is the instruction payload.

---

## Claude Code

Drop the directory in and it is discovered automatically.

Project-scoped:
```bash
cp -r skills/cite-or-abstain .claude/skills/
```

User-scoped, available in every project:
```bash
cp -r skills/cite-or-abstain ~/.claude/skills/
```

Claude reads the `description` of each installed skill and loads the body when it is relevant.
You can also invoke one by name.

---

## Claude API

There is no automatic skill discovery over the raw API — you assemble the prompt yourself.

```python
import anthropic, pathlib

body = pathlib.Path("skills/cite-or-abstain/SKILL.md").read_text(encoding="utf-8")
body = body.split("---", 2)[2]          # strip the YAML header

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=2048,
    system=[
        {
            "type": "text",
            "text": body,
            "cache_control": {"type": "ephemeral"},   # skills are static — cache them
        }
    ],
    messages=[{"role": "user", "content": "..."}],
)
```

Mark skill text with `cache_control` when you send the same skills across many calls. The
content never changes between requests, so it is the ideal cache prefix.

---

## OpenAI

Load the body as a developer message.

```python
from openai import OpenAI
import pathlib

body = pathlib.Path("skills/cite-or-abstain/SKILL.md").read_text(encoding="utf-8")
body = body.split("---", 2)[2]

client = OpenAI()
resp = client.responses.create(
    model="<current-model>",
    input=[
        {"role": "developer", "content": body},
        {"role": "user", "content": "..."},
    ],
)
```

---

## Any local or open-weight model

Concatenate the bodies into the system prompt. Works with llama.cpp, Ollama, vLLM, or anything
else that accepts a system message.

```python
import pathlib

WANTED = ["cite-or-abstain", "retrieval-before-assert", "verify-before-complete"]

def load(name):
    txt = pathlib.Path(f"skills/{name}/SKILL.md").read_text(encoding="utf-8")
    return txt.split("---", 2)[2].strip()

system_prompt = "\n\n---\n\n".join(load(n) for n in WANTED)
```

Smaller models follow short, imperative rules more reliably than long explanatory prose. If a
7B model ignores a skill, cut the body down to its checklist and rules table and drop the
grounding section.

---

## LangChain

```python
from langchain_core.prompts import ChatPromptTemplate
import pathlib

body = pathlib.Path("skills/scope-guard/SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]

prompt = ChatPromptTemplate.from_messages([
    ("system", body),
    ("human", "{input}"),
])
```

---

## Choosing how many to load

Loading all six at once is usually wrong — it costs context and dilutes attention across
instructions that mostly do not apply.

| Task | Load |
|---|---|
| Research, summarisation, factual answers | `cite-or-abstain`, `retrieval-before-assert` |
| Writing or fixing code | `verify-before-complete`, `scope-guard` |
| Financial, security, or irreversible decisions | `self-consistency-check`, `cite-or-abstain` |
| Adding a dependency or third-party repo | `dep-audit` |
| Long autonomous runs | `scope-guard`, `verify-before-complete` |

Relevant instructions placed at the start or end of a long context are followed more reliably
than ones buried in the middle ([Liu et al., arXiv:2307.03172](https://arxiv.org/abs/2307.03172)).
If you load several, put the one that matters most for the current task last.

---

## Adapting them

These encode general practice. Make them yours:

- Replace the example commands in `verify-before-complete` with your actual test and build commands
- Add your repo's specific volatile facts to the `retrieval-before-assert` table
- Adjust the `dep-audit` toolchain to whatever you have installed

A skill that names your real commands gets followed. A generic one gets skimmed.
