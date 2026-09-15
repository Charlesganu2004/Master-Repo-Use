In this repository there are five harnesses. For each one, name its entry script. Then name the three most connected symbols in the repository with the file each is defined in, and for the class Verifier name the function that calls it. Finish with one sentence saying which single file, if changed, would affect the most callers.

Your entire answer must be at most 600 tokens.

graphify is installed and this repository's graph is already built. Run it from the repository root:

  "<graphify>" <command>

Commands: query "<question>" [--budget N], path "A" "B", explain "X", affected "X" [--depth N], god-nodes [--top N] [--json]. The default graph is graphify-out/graph.json in the folder you run it from. Indexing and querying are local: they read the code and the graph file, and call no model.

Answer the question directly. Do not create or modify any files, and do not use the Skill tool.