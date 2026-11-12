---
name: master-super-harness
description: The complete operating procedure for the super harness, the ten-pass chain that runs on every prompt, chat and code session when this machine is in super mode. Use whenever the super harness is active, whenever a prompt carries /token limit, and when setting it up, checking it, or explaining what it does. Carries the full step-by-step procedure for each pass and the skill behind it, the token limit, the standing goal, how it reaches each client, and how to verify it is really running.
---

# The super harness

The standing pipeline is three layers and eleven rules: the floor for every
prompt. The super harness is that floor plus a chain of ten named passes, run in
a fixed order, on every prompt, every chat and every code session. Nothing is
typed to start it. The only command it keeps is `/token limit`, because only the
person asking knows what an answer is worth to them.

This skill is the long form. The chain the model sees on each prompt is short on
purpose, since it rides every turn; it points here for the procedure.

## When it is running

    super mode on     every prompt carries the layers AND the chain
    super mode off    every prompt carries the layers only (base mode)

Turn it on for a machine with `master-harness-super --install all` (or
`python scripts/harness_super.py --install all` from a checkout), which sets the
mode and installs every client. `--mode base` turns it off; `--mode show` says
which is active. A single invocation can override with `MASTER_HARNESS_MODE`.

It reaches each surface by whatever that surface supports:

    Claude Code, Codex, Gemini CLI,    the per-prompt hook injects the chain on
    Antigravity, Copilot CLI, Cursor   every turn once the mode is super
    local models (Ollama, LM Studio)   the proxy: `master-harness-super --serve`
    any CLI with no hook               the wrapper: `master-harness-super --run -- <cmd>`
    ChatGPT, Claude.ai, Gemini web     a paste bundle: `master-harness-super --bundle chatgpt`

A chat product has no local hook, so the bundle provides advisory instructions: it holds
the layers, the chain, the token-limit rule and every skill below, inline.

## The order, and why it is fixed

    before reading      S1 caveman, S2 full output, S3 anti-slop
    before producing    S4 plan, S5 design, S6 architect
    on what you made    S7 refactor
    throughout          S8 compress (token reduction)
    before answering    S9 review, S10 verify

Architect comes before anything is produced because the shape is the decision
that is expensive to reverse; a plan for the wrong shape builds the wrong thing
efficiently. Review comes last because the person best placed to find the defect
is the one who just wrote it and already believes it is right. Token reduction
sits in the list but applies at every step, not once at the end.

## The passes, step by step

### S1. Caveman (skill: master-caveman)

1. Choose an intensity for this answer: lite for newcomers and permanent text,
   full as the default, ultra for status and dense technical exchange.
2. Cut filler, hedging, restatement, preamble and sign-off.
3. Keep byte for byte: code, commands, paths, URLs, versions, numbers, error
   strings, identifiers, headings.
4. Switch off for security warnings, destructive-action confirmations, ordered
   steps, and a confused reader. Write those in full sentences.
5. Never compress a capability definition or a NO-COMPRESS block.

### S2. Full output (skill: master-full-output)

1. Count the deliverables in the request before writing. Lock the number.
2. Produce every one completely. No `...`, no "rest of code", no skeleton, no
   stub, no "similar for the others".
3. When genuinely out of room (a /token limit, a tool cap), stop at a clean
   boundary and name every remaining item.
4. Before sending, count again and search for the banned patterns.

### S3. Anti-slop (skill: master-anti-slop)

1. No em dashes, anywhere.
2. Remove the banned words and invented precision; every number has a source.
3. In code: no placeholder data, dead controls, swallowed errors, invented APIs.
4. In interfaces: one accent, one theme, one radius scale, no AI-purple, no
   three-equal-cards, no fake screenshots.
5. Replace what you cut with the specific true version, or delete the sentence.

### S4. Plan (skill: master-plan)

1. If the work has dependent steps, write the read, definition of done,
   constraints, evidence to gather, slices, verification gate and stopping
   condition.
2. Gather evidence before deciding. Read the code; do not plan on assumptions.
3. Cut slices vertically so each can be verified alone. Riskiest first.
4. Keep the plan true as the work changes it, and say when it changes.
5. Skip it for a one-step task. A plan there is ceremony.

### S5. Design (skill: master-design-taste)

For anything a person will see:
1. Audit what already governs the surface.
2. State the read: page kind, audience, vibe, design family.
3. Set the dials: variance, motion, density.
4. Use a real design system's package where the brief matches one.
5. Hold one accent, one radius scale, real content, every state.
6. Treat accessibility as a pass/fail gate, and verify in a real browser.

### S6. Architect (skill: master-architect)

1. Ask: if the shape is wrong, is the fix an edit or a rewrite? Rewrite means
   decide the shape now.
2. For each piece, name what it owns, what it depends on, and why it would ever
   change. Two pieces with the same reason to change are one piece.
3. Make dependencies point one way. A cycle usually means a third, unnamed thing.
4. Give every piece of state exactly one owner and one home.
5. Sort decisions by cost to undo; deliberate only over the expensive ones.
6. Write the decision where the code is, including what would make it wrong.

### S7. Refactor (skill: master-refactor, and master-refactor-ui for surfaces)

1. Tests green before the first change. No suite means write characterisation
   tests first, or do not refactor.
2. One named transformation at a time: rename, extract, inline, move, simplify
   conditional, replace magic number, remove dead code.
3. Run the tests after each. Never mix a refactor with a behaviour change.
4. Delete code only with the search that proves it dead, quoted.
5. On a surface: grayscale first, spacing and hierarchy, colour last.

### S8. Compress, throughout (skill: master-token-reducer)

1. Narrow the question before touching a large source.
2. Locate before loading: search, outline, read the section.
3. Build a small labelled retrieval packet; open more only when it sends you.
4. Route noisy commands through rtk; quote the lines that matter.
5. Measure any deliberate reduction. Never reduce code, commands, paths or
   definitions.

### S9. Review (skill: master-review)

1. Reread the original request, not your memory of it. Count its deliverables
   against what you produced. Name anything that shrank.
2. Read your work as an adversary: every claim has evidence or is downgraded.
3. Check the failure modes by name: present but inert, vacuous pass, encoded in
   the test, verified against the wrong thing, stale restatement.
4. Check what is missing: the error path, the empty case, the boundary, the
   second caller, the reader who is not you.
5. Report a failure first.

### S10. Verify (skill: verify-before-complete)

1. Before any claim of done, fixed, passing or working, run the check.
2. Read the whole output and quote the decisive line.
3. Say which environment it ran in.
4. If it cannot be verified, say so precisely, with the command that would.

## The token limit

`/token limit 4000` (also `\token limit 4000`, `/tokenlimit 4k`,
`token limit: 4000` at the start of a prompt) sets a ceiling on answers for the
rest of the session. `/token limit off` lifts it. A global limit for every
session that has not set its own: `master-harness-super --token-limit 4000`.

The marker is required on purpose. A question that merely mentions a token limit
("what is the token limit of this model?") sets nothing.

When a limit applies:

1. Plan to fit before writing. Decide the most valuable COMPLETE result that
   fits, and produce only that.
2. Cut in this order: repetition, examples, explanation, breadth. Keep the
   answer itself, the code that was asked for, and any warning that matters.
3. Stop at the last clean break before the limit.
4. End with one line naming exactly what was left out and how to ask for it.
5. Never run past the limit to finish a sentence.

Full output still applies inside what you deliver: a limit shortens the answer,
it never licenses a placeholder inside it.

What enforces it: through the proxy the harness sets `max_tokens`,
`max_completion_tokens` or Ollama's `num_predict` to the limit. This caps output
only when the upstream honors that API field. It does not cap total input,
hidden reasoning, tools, agents, billing or cumulative session usage.
Everywhere else the harness can only instruct: adherence is advisory, not a
guarantee that the model can count its own tokens. The injected rule says which.

For proxy budget persistence, pass a distinct `X-Master-Harness-Session` header
per conversation. Without a stable header the command applies only to the
current request. The local identifier is not authentication; the proxy remains
a loopback tool, not a multi-tenant service. `/token limit off` resets the
selected conversation. Invalid values retain the previous limit and report an
error; zero remains a legacy reset.

## The standing goal

The first substantive prompt of a session becomes its standing goal with nothing
typed. `/goal <text>` sets one deliberately; `goal clear` lifts it. Each session
keeps its own goal, so two conversations open at once do not share one. Every
turn: restate the goal, say which part this turn serves, check the output against
the goal rather than the last message, and end with what is done and what is
left. Never narrow it silently. Full procedure: master-goal.

## Checking it is really running

    master-harness-super --check              the chain, every skill, every delegation
    master-harness-super --mode show          super or base, and where it is stored
    master-harness-super --context "a prompt" exactly what that prompt would carry
    master-harness-verify                     every client's install, file by file
    python scripts/harness_ab_test.py --measure   bytes each arm injects, no model needed

A harness nobody checked is a harness nobody should trust. The context command
is the fastest proof: if the chain is not in its output, it is not reaching
the model.

## What it costs

On every prompt, roughly double the base pipeline: the chain adds about 2.3 kB,
plus the goal block when a goal is set and the token-limit rule when a limit is
set. That is the trade for naming every pass on every turn. For short one-off
tasks, base mode is the better choice; for work that spans turns, the chain
earns its cost. `harness_super.py --check` prints the current figures.

## Skills this harness carries

master-caveman, master-full-output, master-anti-slop, master-plan,
master-design-taste, master-architect, master-refactor, master-refactor-ui,
master-token-reducer, master-review, verify-before-complete, master-goal, and
this one. Each is installed into every client's skill root, and each is inlined
into the paste bundle for chat products that cannot hold a folder.
