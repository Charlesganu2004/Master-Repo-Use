---
name: cite-or-abstain
description: Use when producing factual claims that a reader will act on - research summaries, technical answers, market or financial statements, documentation. Requires every non-obvious factual claim to carry an in-context source, and requires explicit abstention when no source exists.
---

# Cite or Abstain

## The rule

Every factual claim that a reader could act on carries a source, or it is not stated as fact.

Three allowed dispositions for any claim. There is no fourth.

| Disposition | When | How to write it |
|---|---|---|
| **Cited** | A source is in context (retrieved doc, file read this session, tool output, URL fetched) | State the claim, attach the specific source |
| **Flagged as model memory** | No source in context, but you believe it | Prefix with "From training, unverified:" and state the staleness risk |
| **Abstained** | No source and low confidence | "I don't know" / "Not verified" — then say what would settle it |

Silently converting model memory into a confident assertion is the failure this skill exists to prevent.

## What counts as a source

Valid:
- A file you read this session — cite `path:line`
- A tool result in this conversation — cite the tool and what it returned
- A URL you actually fetched — cite the URL
- A retrieved chunk with an identifier

Not valid:
- "It is well known that…"
- A URL you constructed from a pattern but never fetched
- A paper title you recall without checking it exists
- Another model's unverified output
- Your own earlier unsourced claim in this same conversation

That last one matters. Restating an earlier guess does not promote it to fact.

## Citation granularity

Cite the narrowest locator that supports the claim.

```
Bad:   "The retry logic is broken (see the codebase)"
Bad:   "The retry logic is broken (src/)"
Good:  "Retry backoff never resets after success — src/http/retry.ts:88"
```

For documents, cite section not whole document. For a 200-page PDF, "p. 47, §4.2" is a citation; the filename alone is not.

## Numbers get stricter treatment

Any number a reader might put in a spreadsheet, a report, or a trade needs a source or an explicit label as an estimate.

```
Bad:   "This cuts latency by about 40%"
Good:  "Measured 41% p50 latency reduction — bench/results-2026-08.json:12"
Good:  "Rough estimate, unmeasured: order-of-magnitude 30-50% based on the removed round-trip"
```

Never invent a precise-sounding statistic to make a point land harder. A made-up "87%" is worse than "substantially", because it invites the reader to defend a number that does not exist.

## Abstention is a success state

Abstaining is not failure. Answering wrong is failure. When you abstain, be useful about it:

```
I can't verify this from what's in context.

What I'd need: the actual pricing page for that tier, or a doc from this quarter.
What I suspect, unverified: <hypothesis> — treat as a lead, not an answer.
```

Refusal-aware training work (R-Tuning, [arXiv:2311.09677](https://arxiv.org/abs/2311.09677)) and calibration work
([Lin et al., arXiv:2205.14334](https://arxiv.org/abs/2205.14334)) both find models default to answering
rather than declining, even when the answer is unsupported. The default is wrong. Override it deliberately.

## Self-check before sending

Scan your own draft for these and fix each one:

- [ ] Any sentence stating a fact with no source and no hedge
- [ ] Any number without a source or an explicit "estimate" label
- [ ] Any citation pointing at a whole file or whole site rather than a location
- [ ] Any URL you referenced but did not fetch
- [ ] Any claim inherited from an earlier turn that was never sourced
- [ ] Any place where "likely" or "should" is doing work that a real check could do instead

## Grounding

- Attribution as an explicit requirement: [Bohnet et al., *Attributed Question Answering*, arXiv:2212.08037](https://arxiv.org/abs/2212.08037)
- Atomic-fact decomposition for scoring factual precision: [Min et al., *FActScore*, arXiv:2305.14251](https://arxiv.org/abs/2305.14251)
- Faithfulness as a measurable RAG property: [Es et al., *RAGAS*, arXiv:2309.15217](https://arxiv.org/abs/2309.15217)

These describe how to *measure* grounding. This skill is the authoring-time counterpart: write so that a
faithfulness check would pass.

## What this does not do

This reduces unsupported assertions. It does not make retrieved sources correct, and it does not
detect a confidently wrong source. Pair with [retrieval-before-assert](../retrieval-before-assert/SKILL.md)
to get sources in context, and [self-consistency-check](../self-consistency-check/SKILL.md) for
high-stakes claims where a single source is not enough.
