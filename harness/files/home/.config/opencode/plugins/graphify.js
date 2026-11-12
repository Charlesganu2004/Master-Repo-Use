// graphify OpenCode plugin, one file for OpenCode V2 (setup) and V1 (server).
// Once per location, prepends a short knowledge graph reminder to the first
// shell command when graphify-out/graph.json exists.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// It is echoed by the shell, so either would be evaluated as code. Use ';' not
// '&&': Windows PowerShell 5.1 rejects '&&' as a statement separator.
import { existsSync } from "fs";
import { join } from "path";

const REMINDER =
  "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context.";

const SHELL_TOOLS = new Set(["bash", "shell"]);

const hasGraph = (directory) =>
  existsSync(join(directory, "graphify-out", "graph.json"));

const withReminder = (command) => 'echo "' + REMINDER + '" ; ' + command;

export default {
  id: "graphify",

  async setup(ctx) {
    const directory = ctx.location.directory;
    let reminded = false;

    await ctx.tool.hook("execute.before", (event) => {
      if (reminded || !SHELL_TOOLS.has(event.tool)) return;
      if (typeof event.input?.command !== "string") return;
      if (!hasGraph(directory)) return;

      event.input = { ...event.input, command: withReminder(event.input.command) };
      reminded = true;
    });
  },

  async server({ directory }) {
    let reminded = false;

    return {
      "tool.execute.before": async (input, output) => {
        if (reminded || !SHELL_TOOLS.has(input.tool)) return;
        if (typeof output.args?.command !== "string") return;
        if (!hasGraph(directory)) return;

        output.args.command = withReminder(output.args.command);
        reminded = true;
      },
    };
  },
};
