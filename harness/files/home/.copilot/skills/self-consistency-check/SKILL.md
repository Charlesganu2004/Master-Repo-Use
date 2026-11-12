---
name: self-consistency-check
description: Use for high-stakes answers where being wrong is expensive - financial figures, security verdicts, medical or legal facts, irreversible operations, load-bearing architectural decisions. Samples the reasoning more than once and reconciles disagreement instead of trusting one pass.
---

# Self-Consistency Check

## When to spend the extra passes

This costs real time and tokens. Use it where a wrong answer is expensive, not everywhere.

**Use it for:**
- Numbers someone will act on — costs, position sizes, capacity estimates, rates
- Security verdicts — "this repo is safe to add", "this input is sanitised"
- Irreversible operations — deletions, migrations, pushes, trades
- Load-bearing architecture decisions
- Any claim where you notice yourself uncertain but about to sound confident

**Skip it for:**
- Reversible, cheap-to-check work
- Anything where running the actual command is faster than reasoning twice (just run it —
  see [verify-before-complete](../verify-before-complete/SKILL.md))
- Formatting, naming, style

## The method

1. **Answer the question independently more than once.** Genuinely independently — do not
   re-read your first answer and check it, which mostly reproduces its errors. Where possible,
   approach from a different direction each time.
2. **Compare the answers.**
3. **Converged** → confidence is warranted. Report it.
4. **Diverged** → this is signal, not noise. Do not average. Do not pick the one you like.
   Find out which is right, or report the disagreement explicitly.

Divergence is the useful output. A question that yields three different answers across three
passes is a question you do not currently know the answer to, regardless of how confident any
single pass sounded.

## Getting genuine independence

Re-deriving the same way twice buys almost nothing. Vary the approach:

| Question type | Independent angles |
|---|---|
| Numeric | Forward calculation; reverse-check from the result; order-of-magnitude sanity check |
| "Is this code correct?" | Read the happy path; hunt the edge cases; try to construct a failing input |
| "Is this dependency safe?" | Check the code; check the maintainer and history; check what it does at install time |
| "Will this design work?" | Argue for it; argue against it; ask what breaks first at 10x load |
| Factual | Recall it; retrieve it; check whether the retrieved source actually says that |

## Adversarial variant

For security and safety verdicts, do not sample neutrally — sample *against* the conclusion.

Instead of "is this safe?" ask "assume this is malicious; what would that look like, and is
it present?" Default the answer to unsafe and require evidence to clear it. A neutral prompt
run three times tends to agree with itself; a refutation-shaped prompt surfaces what the
neutral one missed.

Rule of thumb: if a majority of independent refutation attempts succeed, the original claim
does not survive.

## Reporting divergence honestly

```
Two passes disagree on the position-size cap.
  Pass A: $2.00  (10% of the $20 ceiling)
  Pass B: $1.00  (assumes the $10 per-account limit binds first)
The disagreement is over which ceiling applies. That's the real question — resolve it
before sizing anything. I have not established which is correct.
```

Never silently pick one and present it as settled.

## Grounding

- Sampling multiple reasoning paths and marginalising over them beats single greedy decoding:
  [Wang et al., *Self-Consistency Improves Chain of Thought Reasoning*, arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
- Disagreement across independent samples is itself a hallucination signal — the core insight
  behind [Manakul et al., *SelfCheckGPT*, arXiv:2303.08896](https://arxiv.org/abs/2303.08896):
  sampled responses tend to agree on facts the model actually knows and diverge on ones it
  fabricated.

Note what these papers do and do not say. Self-consistency measurably improves accuracy on
reasoning benchmarks, and sampling divergence correlates with fabrication. Neither gives a
fixed hallucination-reduction rate that transfers across models and tasks — the gains reported
are benchmark-specific. Treat convergence as *evidence of* reliability, not proof of it.

## Self-check

- [ ] Is this actually high-stakes, or am I burning passes on something cheap to check?
- [ ] Were my passes genuinely independent, or did I just re-read pass one?
- [ ] For a safety verdict: did I try to refute it, or only to confirm it?
- [ ] If they diverged, did I resolve it or paper over it?
