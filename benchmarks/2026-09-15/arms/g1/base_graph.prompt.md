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
12. Adding anything third-party: run the dep-audit path first. Catalogued is not vetted, and scripts/install_catalog_skill.py is the reviewed route into a skill root.
STANDING GOAL, carried across turns until the person who set it lifts it.
    GOAL: In the repository at <repo>, name the three most connected symbols (the architectural hubs) and the file each one is defined in. Give the three as a short list.
    Restate it in one line before reading the request, say which part this turn
    serves, check what you produced against the GOAL rather than the last
    message, and end by saying what is done and what is left. Never narrow it
    silently: a blocked part is reported as blocked, and every unblocked part is
    finished. Not lifted by a long session, a token budget, a compaction pass, or
    a subagent that was not told. It was set from the first task of this session without a command, and it is lifted the same way: say so, or type goal clear.
15. TOKEN LIMIT: 400 tokens for this response, set with /token limit. A ceiling, not a target.
    Plan to fit before writing: choose the most valuable COMPLETE result that fits in 400 tokens and produce only that. Cut repetition, then examples, then explanation, then breadth; keep the answer itself, the code that was asked for, and any warning that matters.
    Stop at the last clean break before the limit and end with one line saying exactly what was left out and how to ask for it. Never run past it to finish a thought. FULL OUTPUT still forbids placeholders inside what you do deliver. This client cannot cap tokens itself. This is advisory, not an enforced output or total-token billing limit; do not claim precise counting or guaranteed enforcement.
    Lift it with /token limit off.
</system-reminder>

/token limit 400 In the repository at <repo>, name the three most connected symbols (the architectural hubs) and the file each one is defined in. Give the three as a short list.

graphify 0.9.61 is installed on this machine and the repository's graph is already built. Run it from the repository root:

  "<graphify>" <command>

Commands: query "<question>" [--budget N], path "A" "B", explain "X", affected "X" [--depth N], god-nodes [--top N] [--json]. The default graph is graphify-out/graph.json in the folder you run it from; pass --graph for another. Indexing and querying are local: they parse the code and read the graph file, and call no model.

Answer the question directly. Do not create or modify any files, and do not use the Skill tool.