In this repository, trace how a user's prompt becomes injected context: name the hook file that does it, the function inside it that builds the context, and the file that adds the super harness chain on top. Then name the three most connected symbols in the repository and the file each is defined in.

Your entire answer must be at most 600 tokens.

graphify is installed and this repository's graph is already built. Run it from the repository root:

  "<graphify>" <command>

Commands: query "<question>" [--budget N], path "A" "B", explain "X", affected "X" [--depth N], god-nodes [--top N] [--json]. The default graph is graphify-out/graph.json in the folder you run it from. Indexing and querying are local: they read the code and the graph file, and call no model.

Answer the question directly. Do not create or modify any files, and do not use the Skill tool.