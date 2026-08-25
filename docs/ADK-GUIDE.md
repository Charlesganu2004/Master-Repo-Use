# Agent Development Kits (ADKs)

An **ADK** is a first-party, vendor-maintained framework for building agents: model calls, tool
registration, memory, multi-agent handoff, and a deployment story, in one supported package.

The distinction that matters: ADKs are the *vendor-supported successors* to the previous
generation of community agent frameworks. `microsoft/agent-framework` is literally the merger of
AutoGen and Semantic Kernel. If you are picking a framework in 2026, start here — not with a
2024-era community project.

Catalog lane: [`repo-lists/adk-agent-kits.txt`](../repo-lists/adk-agent-kits.txt)

## Which one

| You want | Use | Why |
|---|---|---|
| Python agents, Google/Vertex stack | `google/adk-python` | Largest ADK by adoption; strongest docs and samples |
| Java/enterprise JVM | `google/adk-java` | Same model, JVM-native |
| A browser UI to debug agents | `google/adk-web` | Dev UI for ADK agents; pairs with either runtime |
| Working examples first | `google/adk-samples` | Read this before writing anything |
| .NET, or you already use Semantic Kernel | `microsoft/agent-framework` | The supported successor to AutoGen + SK; ships .NET and Python weekly |
| You are on OpenAI models | `openai/openai-agents-python` | Thin, unopinionated, handoff-oriented |

## The AutoGen question

`microsoft/autogen` is in this catalog and is **superseded**. The evidence, checked 2026-08-25:

- AutoGen's last release was `python-v0.7.5` on **2025-09-30**; last push 2026-04-15.
- `microsoft/agent-framework` released `dotnet-1.19.0` on **2026-08-22** and ships roughly weekly.

Existing AutoGen code is not broken and does not need an emergency migration. But **new** work
should start on `agent-framework`. The catalog keeps AutoGen as a reference entry with that note
attached rather than silently deleting it — see
[`docs/CATALOG-TRIAGE-2026-08-25.md`](CATALOG-TRIAGE-2026-08-25.md).

## Choosing between an ADK and raw API calls

Reach for an ADK when you need **at least two** of:

- multi-agent handoff or delegation
- durable session/memory across turns
- a tool registry shared by several agents
- a managed deployment target (Vertex Agent Engine, Azure AI Foundry)

For a single agent with three tools, an ADK is overhead. Call the API directly.

## Minimal Google ADK example

```bash
pip install google-adk
```

```python
from google.adk.agents import Agent


def get_ram_gb() -> dict:
    """Report installed system RAM so the agent can size a local model."""
    import psutil
    return {"ram_gb": round(psutil.virtual_memory().total / 1024**3)}


root_agent = Agent(
    name="hardware_advisor",
    model="gemini-2.0-flash",
    instruction=(
        "Advise which local model fits this machine. Call get_ram_gb first; "
        "never guess the amount of memory."
    ),
    tools=[get_ram_gb],
)
```

Run the dev UI against it:

```bash
adk web
```

## Minimal Microsoft Agent Framework example

```bash
pip install agent-framework
```

```python
import asyncio
from agent_framework.openai import OpenAIChatClient


async def main() -> None:
    agent = OpenAIChatClient().create_agent(
        instructions="You size local models against available RAM.",
        name="hardware_advisor",
    )
    print(await agent.run("What fits in 16 GB?"))


asyncio.run(main())
```

## Interop: MCP is the tool layer

All three ADKs speak **MCP**, so tools are portable even when frameworks are not. Register a tool
once as an MCP server and every ADK above can call it. That is the cheapest hedge against
picking the wrong framework — see [`docs/MCP-SERVERS.md`](MCP-SERVERS.md).

## Cost note

ADK samples default to hosted models. Before running the samples in a loop, read
[`docs/TOKEN-BUDGET.md`](TOKEN-BUDGET.md) — and for local development, point the ADK at an Ollama
endpoint instead. See [`docs/LOCAL-MODEL-HARDWARE.md`](LOCAL-MODEL-HARDWARE.md) for what your
machine can host.
