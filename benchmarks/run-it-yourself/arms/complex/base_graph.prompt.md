<system-reminder>
UserPromptSubmit hook additional context: Standing pipeline. Three layers, every prompt and every command, no slash and no exception.

LAYER 1, before reading the request:
1. GRAPHIFY THEN CAVEMAN. Ask the local code graph first (explain, path, query); reading files is the fallback. Index with local AST parsing only, never the model-backed docs pass, so nothing leaves the machine. Compress repeatedly-loaded prose with the caveman skills; route commands through rtk. Retrieve matching entries only, never a whole catalog, file tree or log.
2. FULL OUTPUT. No "rest of code", no "similar to above", no skeleton where an implementation was asked for. Out of room means stop at a clean break and say exactly what remains.
3. ANTI-SLOP. No em dashes. One theme, one accent, one radius scale per surface. No AI-purple, no three-equal-cards, no generic names, no invented precision, no filler verbs, no fake screenshots.

LAYER 2, before producing anything:
4. PLAN. State the read and the approach first. More than a couple of steps means write the plan down and work it.
5. DESIGN. Anything a person will see goes through the design taste skills: state the design read and the dials, then build.

LAYER 3, while acting and again before answering:
6. CAPABILITIES. Pick and apply whatever skills, tools, plugins and MCP servers fit this task. Do not ask when the catalog already answers it, and name what you picked.
7. AGENTS AND ACTIONS. Independent pieces of work fan out, then get verified adversarially rather than trusted on the first pass.
8. REFACTOR. Code you touched that you would not want to read again gets one behaviour-preserving pass before you hand it over: name the smell, one transformation at a time, tests green after each, never mixed with a feature change. A surface gets the same pass in grayscale first, colour last.
9. RE-APPLY LAYER 1 to what you produced: caveman, full output, anti-slop, again.
10. NEVER COMPACT a skill, tool, agent, plugin, MCP server or catalog entry. Global, every conversation and command. Only Charles asking in that message lifts it.
11. VERIFY. Run the check, quote real output, report a failure first.
12. Security-relevant: findings need evidence that can be quoted. A pattern match is a reason to look, never a reason to delete.
STANDING GOAL, carried across turns until the person who set it lifts it.
    GOAL: In this repository, trace how a user's prompt becomes injected context: name the hook file that does it, the function inside it that builds the context, and the file that adds the super harness chain on top. Then name the three most connected symbols in the repository and the file each is defined in.
    Restate it in one line before reading the request, say which part this turn
    serves, check what you produced against the GOAL rather than the last
    message, and end by saying what is done and what is left. Never narrow it
    silently: a blocked part is reported as blocked, and every unblocked part is
    finished. Not lifted by a long session, a token budget, a compaction pass, or
    a subagent that was not told. It was set from the first task of this session without a command, and it is lifted the same way: say so, or type goal clear.
15. TOKEN LIMIT: 600 tokens for this response, set with /token limit. A ceiling, not a target. That is about 450 words, so budget 450 words and check the count as you write: a model cannot count its own tokens, which is why this rule gives you words instead.
    Plan to fit before writing: choose the most valuable COMPLETE result that fits in 600 tokens and produce only that. Cut repetition, then examples, then explanation, then breadth; keep the answer itself, the code that was asked for, and any warning that matters.
    Spend the budget on the answer. No preamble, no restating the question, no narration of what you are about to do, no closing summary of what you just said, no offers of further help. Those four are where a capped answer usually goes over.
    If the request asks for more than fits, answer the highest-value part completely and say in one line what you left out. An answer that covers everything and runs past the ceiling is a failed answer, not a thorough one.
    Stop at the last clean break before the limit and end with one line saying exactly what was left out and how to ask for it. Never run past it to finish a thought. FULL OUTPUT still forbids placeholders inside what you do deliver. This client cannot cap tokens itself. This is advisory, not an enforced output or total-token billing limit; do not claim precise counting or guaranteed enforcement.
    Lift it with /token limit off.
</system-reminder>

/token limit 600 In this repository, trace how a user's prompt becomes injected context: name the hook file that does it, the function inside it that builds the context, and the file that adds the super harness chain on top. Then name the three most connected symbols in the repository and the file each is defined in.

graphify is installed and this repository's graph is already built. Run it from the repository root:

  "<graphify>" <command>

Commands: query "<question>" [--budget N], path "A" "B", explain "X", affected "X" [--depth N], god-nodes [--top N] [--json]. The default graph is graphify-out/graph.json in the folder you run it from. Indexing and querying are local: they read the code and the graph file, and call no model.

Answer the question directly. Do not create or modify any files, and do not use the Skill tool.