# Skills

Portable agent skills for this repo. Plain Markdown with a two-field YAML header — they work
as Claude Code skills, as an OpenAI developer message, or as a system-prompt prefix for any
open-weight model. See [PORTABLE-USAGE.md](PORTABLE-USAGE.md) for how to load them into each.

## The skills

| Skill | Use when |
|---|---|
| [cite-or-abstain](cite-or-abstain/SKILL.md) | Producing factual claims a reader will act on |
| [retrieval-before-assert](retrieval-before-assert/SKILL.md) | The answer could have changed since training |
| [verify-before-complete](verify-before-complete/SKILL.md) | About to claim something is done, fixed, or passing |
| [self-consistency-check](self-consistency-check/SKILL.md) | High-stakes answer where being wrong is expensive |
| [scope-guard](scope-guard/SKILL.md) | Request is ambiguous, or larger than it first appears |
| [dep-audit](dep-audit/SKILL.md) | Adding a third-party repo, package, or MCP server |
| [catalog-freshness](catalog-freshness/SKILL.md) | Checking whether catalogued repos are still maintained |

The first four target hallucination and unsupported confidence from different angles:

```text
retrieval-before-assert   get real sources into context
        |
cite-or-abstain           every claim carries one, or is marked unverified
        |
self-consistency-check    high-stakes claims sampled more than once
        |
verify-before-complete    "done" requires observed output, not inference
```

`scope-guard` covers a different failure — answering a question nobody asked, or quietly
answering a smaller one.

`dep-audit` and `catalog-freshness` are the two halves of keeping this catalog trustworthy:
`dep-audit` gates what comes in, `catalog-freshness` catches what rots after it is already
here. Both are backed by runnable tooling — [docs/SECURITY-SCANNING.md](../docs/SECURITY-SCANNING.md)
and [scripts/check_freshness.py](../scripts/check_freshness.py), the latter running weekly via
[.github/workflows/repo-freshness.yml](../.github/workflows/repo-freshness.yml).

## What these do, and what they don't

They are prompt-level controls. They make a model retrieve before asserting, attach sources,
check its own claims against real output, and decline when it has nothing to stand on. In
practice that removes a large share of confident-but-unsupported output.

They do **not** come with a guaranteed reduction figure, and this repo will not print one.
The underlying research reports gains that are real but benchmark-specific and
model-specific — self-consistency's improvements are measured per-task
([Wang et al., arXiv:2203.11171](https://arxiv.org/abs/2203.11171)), Chain-of-Verification's
likewise ([Dhuliawala et al., arXiv:2309.11495](https://arxiv.org/abs/2309.11495)). No
published result supports a single portable percentage across models and tasks, so quoting
one would be exactly the kind of unsourced number `cite-or-abstain` exists to prevent.

They also cannot fix a wrong source. If retrieval returns a confidently incorrect document,
grounding to it produces a well-cited wrong answer. Source quality is upstream of all of this.

## Each skill's structure

- **The rule** — one sentence, the thing to actually do
- **Procedure or decision table** — how to apply it
- **Failure modes** — the specific ways it gets skipped
- **Grounding** — the research, cited with arXiv links
- **Self-check** — checklist to run before sending output

## Related

- [agents/](../agents/) — full agent definitions; skills are narrower and composable
- [docs/SECURITY.md](../docs/SECURITY.md) — repo-level agent injection and MCP scoping rules
- [docs/SECURITY-SCANNING.md](../docs/SECURITY-SCANNING.md) — the scanner toolchain
