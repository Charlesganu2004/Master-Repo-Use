# Quantum Computing Lane

Quantum is a standalone lane in this repo. It can also connect to the agent stack as an optional sidecar, especially for optimization, sampling, quantum machine learning, and portfolio research.

For stock, investing, day-trading, and agent/plugin workflows, use [Quantum trading and investing](QUANTUM-TRADING.md).

## When To Use Quantum Here

Use quantum when the goal is one of these:

- Learn quantum programming with simulators first.
- Test quantum finance or portfolio optimization examples.
- Compare quantum-inspired optimization against classical baselines.
- Build a small quantum tool that an agent can call through Python, an API bridge, or MCP.
- Create a demo that explains where quantum might help and where it does not.

Do not force quantum into every agent workflow. Most agent tasks are better served by normal tools, RAG, memory, and cost controls.

## Flow

```text
Standalone experiment
  -> Qiskit, PennyLane, Cirq, Q#, Braket, D-Wave, or CUDA-Q
  -> simulator
  -> metrics and comparison
  -> optional hardware or cloud job
```

```text
Integrated sidecar
  -> agent asks for optimization or QML experiment
  -> API/MCP bridge validates inputs
  -> quantum runner executes simulator/hardware job
  -> result is compared with a classical baseline
  -> agent summarizes result and caveats
```

## Repos

| Repo | Use it when | Fast start |
| --- | --- | --- |
| [Qiskit/qiskit](https://github.com/Qiskit/qiskit) | You want IBM's open-source quantum SDK. | `python -m pip install qiskit` |
| [qiskit-community/qiskit-finance](https://github.com/qiskit-community/qiskit-finance) | You want quantum finance examples. | `python -m pip install qiskit-finance` |
| [qiskit-community/qiskit-machine-learning](https://github.com/qiskit-community/qiskit-machine-learning) | You want quantum machine learning. | `python -m pip install qiskit-machine-learning` |
| [qiskit-community/qiskit-optimization](https://github.com/qiskit-community/qiskit-optimization) | You want optimization workflows. | `python -m pip install qiskit-optimization` |
| [PennyLaneAI/pennylane](https://github.com/PennyLaneAI/pennylane) | You want quantum differentiable programming and QML. | `python -m pip install pennylane` |
| [PennyLaneAI/pennylane-qiskit](https://github.com/PennyLaneAI/pennylane-qiskit) | You want PennyLane with Qiskit devices. | `python -m pip install pennylane-qiskit` |
| [quantumlib/Cirq](https://github.com/quantumlib/Cirq) | You want Google's Python framework for NISQ circuits. | `python -m pip install cirq` |
| [microsoft/qsharp](https://github.com/microsoft/qsharp) | You want Q#, resource estimation, and Quantum Katas. | `dotnet tool install --global Microsoft.Quantum.IQSharp` or follow current QDK docs. |
| [aws/amazon-braket-sdk-python](https://github.com/aws/amazon-braket-sdk-python) | You want Amazon Braket quantum device access. | `python -m pip install amazon-braket-sdk` |
| [dwavesystems/dwave-ocean-sdk](https://github.com/dwavesystems/dwave-ocean-sdk) | You want D-Wave Ocean tools. | `python -m pip install dwave-ocean-sdk` |
| [unitaryfund/mitiq](https://github.com/unitaryfund/mitiq) | You want quantum error mitigation tools. | `python -m pip install mitiq` |
| [NVIDIA/cuda-quantum](https://github.com/NVIDIA/cuda-quantum) | You want heterogeneous quantum-classical workflows. | Follow CUDA-Q install docs for your OS. |
| [qosf/awesome-quantum-software](https://github.com/qosf/awesome-quantum-software) | You want a larger quantum software discovery list. | Read by category. |

## Integration With Everything

| Integration | How it works |
| --- | --- |
| Quantum + agents | Agent calls a small Python function, API endpoint, or MCP tool that runs a simulator. |
| Quantum + RAG | RAG retrieves paper notes, algorithm docs, and experiment logs before the agent explains results. |
| Quantum + memory | Memory stores experiment assumptions, baseline metrics, and hardware/simulator choices. |
| Quantum + trading | Use Qiskit Finance or optimization libraries for portfolio experiments, always compared against classical baselines. |
| Quantum + Copilot Studio | Copilot Studio calls an API bridge that runs a bounded experiment and returns a short explanation. |
| Quantum + cost controls | Simulators can be local; hardware/cloud jobs need budget checks and explicit approval. |
| Quantum + pitch decks | Quantum demos can feed Slidev/Marpit as standalone presentation material. |

## Small Combos

| Combo | Good first experiment |
| --- | --- |
| Qiskit + qiskit-finance | Portfolio optimization demo. |
| PennyLane + scikit-learn | Compare a QML classifier with a classical classifier. |
| Cirq + notebook | Build and simulate a small circuit. |
| Q# + resource estimator | Estimate resources for a sample quantum algorithm. |
| Braket SDK + local simulator | Prepare cloud-compatible experiments locally. |
| D-Wave Ocean + optimization | Try a small binary optimization problem. |
| Qiskit + MCP Python server | Expose one safe `run_portfolio_demo` tool to an agent. |
| Quantum trading plugin | Use [plugins/quantum-trading-agent](../plugins/quantum-trading-agent/README.md) as a paper-trading-first scaffold. |

## One-Liners

Clone quantum repos, PowerShell:

```powershell
$MasterRepo = Read-Host "Path to Master-Repo-Use"; $LanePath = Read-Host "Folder where quantum repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\quantum-computing.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone quantum repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where quantum repos should be cloned: " lane_path; mkdir -p "$lane_path"; grep -vE '^(#|$)' "$master_repo/repo-lists/quantum-computing.txt" | while read -r repo; do gh repo clone "$repo" "$lane_path/${repo/\//-}"; done
```

Install a Qiskit finance lab:

```powershell
$LabPath = Read-Host "Where should the Qiskit finance lab be created?"; New-Item -ItemType Directory -Force $LabPath | Out-Null; Set-Location $LabPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip qiskit qiskit-finance qiskit-optimization matplotlib pandas
```

Install in WSL/Bash:

```bash
read -rp "Where should the Qiskit finance lab be created? " lab_path; mkdir -p "$lab_path"; cd "$lab_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip qiskit qiskit-finance qiskit-optimization matplotlib pandas
```

Install a PennyLane lab:

```powershell
python -m pip install --user pennylane pennylane-qiskit scikit-learn matplotlib
```

Run a tiny Qiskit smoke test:

```powershell
python -c "from qiskit import QuantumCircuit; qc=QuantumCircuit(2); qc.h(0); qc.cx(0,1); print(qc)"
```

Run a tiny PennyLane smoke test:

```bash
python -c "import pennylane as qml; print(qml.about())"
```

## Guardrails

- Simulate locally before using paid quantum cloud resources.
- Compare every quantum result with a classical baseline.
- Keep problem sizes tiny until the workflow is proven.
- Do not claim quantum advantage without evidence.
- Log costs for Braket, IBM Quantum, Azure Quantum, D-Wave, or other cloud/hardware providers.
