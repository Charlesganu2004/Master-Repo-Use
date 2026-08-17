# Repo Health & Status Tracking

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

This file tracks the health of every repo in the catalog. Run the automated check with Iris (see [agents/repo-issue-iris.md](../agents/repo-issue-iris.md)) or run the manual commands below.


---

## Status Definitions

| Status | Meaning | What to do |
|---|---|---|
| `active` | Committed to in the last 90 days | Safe to use |
| `slow` | Last commit 90–365 days ago | Use with caution, monitor for updates |
| `stale` | No commits in 1+ years | Research alternatives before adopting |
| `deprecated` | Maintainer explicitly says deprecated | Use replacement listed in this doc |
| `archived` | GitHub archived flag is set | Use replacement listed in this doc |
| `unmaintained` | No issue responses, no commits in 18+ months | Do not use for new projects |

---

## Manual Health Check

PowerShell — check one repo:

```powershell
$Repo = Read-Host "Enter owner/repo (e.g. HKUDS/LightRAG)"
$Token = Read-Host "GitHub token (or leave blank for public repos)"
$Headers = if ($Token) { @{Authorization = "Bearer $Token"} } else { @{} }
$Info = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo" -Headers $Headers
[PSCustomObject]@{
    Repo = $Repo
    Archived = $Info.archived
    LastPush = $Info.pushed_at
    OpenIssues = $Info.open_issues_count
    Stars = $Info.stargazers_count
} | Format-Table
```

WSL/Bash — check one repo:

```bash
repo="HKUDS/LightRAG"  # change this
curl -s "https://api.github.com/repos/$repo" | jq '{archived: .archived, last_push: .pushed_at, open_issues: .open_issues_count, stars: .stargazers_count}'
```

GitHub CLI — bulk check from repo list:

```bash
read -rp "Path to Master-Repo-Use: " master_repo
grep -vE '^(#|$)' "$master_repo/repo-lists/all-curated.txt" | while read -r repo; do
  result=$(gh api "repos/$repo" --jq '{archived: .archived, pushed: .pushed_at, issues: .open_issues_count}' 2>/dev/null)
  echo "$repo: $result"
done
```

---

## Automated Check with Iris

Start Iris in Propose mode and ask:

```
Iris, run a health check on all repos in repo-lists/all-curated.txt. Write the results to issues/ for my review.
```

Iris will output a table and wait for your approval before taking any action.

---

## Status Table

Run the health check to populate this table. Iris writes directly to this file in Act mode.

| Repo | Status | Last Push | Notes | Replacement |
|---|---|---|---|---|
| bradygaster/squad | _check needed_ | | | |
| HKUDS/LightRAG | _check needed_ | | | |
| microsoft/agents | _check needed_ | | | |
| modelcontextprotocol/servers | _check needed_ | | | |
| alpacahq/alpaca-py | _check needed_ | | | |
| OpenBB-finance/OpenBB | _check needed_ | | | |
| Qiskit/qiskit | _check needed_ | | | |
| infracost/infracost | _check needed_ | | | |
| ooples/token-optimizer-mcp | _check needed_ | | | |
| yvgude/lean-ctx | _check needed_ | | | |

_Run `Iris: health check` to populate all rows._

---

## Replacement Candidates

Repos that are known to be stale and their recommended replacements:

| Archived/Stale Repo | Recommended Replacement | Notes |
|---|---|---|
| (populated by Iris on first run) | | |

---

## How Iris Updates This File

In Act mode, Iris:
1. Runs the bulk GitHub API check.
2. Writes status and last-push date for every row.
3. Flags any repo with archived=true as `archived`.
4. Flags any repo with no commits in 365+ days as `stale`.
5. Searches the replacement candidates table and fills in replacements where known.
6. Writes a log entry to `issues/iris-YYYY-MM-DD.md` with a summary of what changed.

---

## Security Advisories

GitHub CLI — check security advisories for a repo:

```bash
gh api repos/HKUDS/LightRAG/security-advisories --jq '.[].ghsa_id' 2>/dev/null || echo "No advisories or private repo"
```

Repos with open security advisories are flagged Critical by Sentinel. See [agents/security-sentinel.md](../agents/security-sentinel.md).

---

<!-- FRESHNESS:START -->

**Last automated check:** 2026-08-17 · **Repos:** 234 · archived 4 · stale 9 · slow 41 · active 180

Regenerate with `python scripts/check_freshness.py`. Runs weekly via `.github/workflows/repo-freshness.yml`.

### Needs attention (13)

| Repo | Status | Last push | Age (days) | Listed in |
| --- | --- | --- | --- | --- |
| [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | `archived` | 2026-08-13 | — | all-curated.txt, article-discoveries.txt |
| [YuhaoLin2005/compact-counter-concept](https://github.com/YuhaoLin2005/compact-counter-concept) | `archived` | 2026-07-02 | — | all-curated.txt, article-discoveries.txt |
| [qiskit-community/qiskit-optimization](https://github.com/qiskit-community/qiskit-optimization) | `archived` | 2026-07-12 | — | all-curated.txt, quantum-computing.txt, quantum-finance-trading.txt |
| [tastytrade/tastytrade-sdk-python](https://github.com/tastytrade/tastytrade-sdk-python) | `archived` | 2026-03-13 | — | all-curated.txt, broker-app-integrations.txt |
| [ZongqianLi/Prompt-Compression-Survey](https://github.com/ZongqianLi/Prompt-Compression-Survey) | `stale` | 2025-05-18 | 456 | all-curated.txt, context-token-management.txt |
| [aarora79/aws-cost-explorer-mcp-server](https://github.com/aarora79/aws-cost-explorer-mcp-server) | `stale` | 2025-04-14 | 490 | all-curated.txt, cost-reduction.txt |
| [alexgolec/schwab-py](https://github.com/alexgolec/schwab-py) | `stale` | 2025-08-04 | 378 | all-curated.txt, broker-app-integrations.txt |
| [financial-datasets/mcp-server](https://github.com/financial-datasets/mcp-server) | `stale` | 2025-06-05 | 438 | all-curated.txt, trading-agent-risk-tools.txt |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | `stale` | 2025-07-29 | 384 | all-curated.txt, spatial-3d.txt |
| [oyi77/Crypto-RL-Trading-Bot](https://github.com/oyi77/Crypto-RL-Trading-Bot) | `stale` | 2025-04-08 | 496 | all-curated.txt, day-trading-bots.txt |
| [qiskit-community/ibm-quantum-challenge-fall-2021](https://github.com/qiskit-community/ibm-quantum-challenge-fall-2021) | `stale` | 2025-02-14 | 549 | all-curated.txt, quantum-finance-trading.txt |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | `stale` | 2025-08-05 | 377 | all-curated.txt, spatial-world-models.txt |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | `stale` | 2025-07-17 | 396 | all-curated.txt, spatial-world-models.txt |

### All repos

| Repo | Status | Last push | Stars |
| --- | --- | --- | --- |
| [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | `archived` | 2026-08-13 | 55378 |
| [qiskit-community/qiskit-optimization](https://github.com/qiskit-community/qiskit-optimization) | `archived` | 2026-07-12 | 285 |
| [tastytrade/tastytrade-sdk-python](https://github.com/tastytrade/tastytrade-sdk-python) | `archived` | 2026-03-13 | 106 |
| [YuhaoLin2005/compact-counter-concept](https://github.com/YuhaoLin2005/compact-counter-concept) | `archived` | 2026-07-02 | 0 |
| [aarora79/aws-cost-explorer-mcp-server](https://github.com/aarora79/aws-cost-explorer-mcp-server) | `stale` | 2025-04-14 | 127 |
| [alexgolec/schwab-py](https://github.com/alexgolec/schwab-py) | `stale` | 2025-08-04 | 461 |
| [financial-datasets/mcp-server](https://github.com/financial-datasets/mcp-server) | `stale` | 2025-06-05 | 2279 |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | `stale` | 2025-07-29 | 11904 |
| [oyi77/Crypto-RL-Trading-Bot](https://github.com/oyi77/Crypto-RL-Trading-Bot) | `stale` | 2025-04-08 | 7 |
| [qiskit-community/ibm-quantum-challenge-fall-2021](https://github.com/qiskit-community/ibm-quantum-challenge-fall-2021) | `stale` | 2025-02-14 | 142 |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | `stale` | 2025-08-05 | 738 |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | `stale` | 2025-07-17 | 229 |
| [ZongqianLi/Prompt-Compression-Survey](https://github.com/ZongqianLi/Prompt-Compression-Survey) | `stale` | 2025-05-18 | 36 |
| [aitrados/finance-trading-ai-agents-mcp](https://github.com/aitrados/finance-trading-ai-agents-mcp) | `slow` | 2025-11-19 | 64 |
| [allenai/molmoact](https://github.com/allenai/molmoact) | `slow` | 2026-05-11 | 380 |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | `slow` | 2025-12-20 | 1628 |
| [bradygaster/CustomAgent](https://github.com/bradygaster/CustomAgent) | `slow` | 2025-10-24 | 2 |
| [bradygaster/dotnet-cloud-native-build-2023](https://github.com/bradygaster/dotnet-cloud-native-build-2023) | `slow` | 2025-10-21 | 163 |
| [bradygaster/MultiAgent](https://github.com/bradygaster/MultiAgent) | `slow` | 2025-11-20 | 9 |
| [bradygaster/Squad-IRL](https://github.com/bradygaster/Squad-IRL) | `slow` | 2026-03-12 | 45 |
| [bukosabino/ta](https://github.com/bukosabino/ta) | `slow` | 2026-03-18 | 5142 |
| [coinbase/cdp-sdk-python](https://github.com/coinbase/cdp-sdk-python) | `slow` | 2025-10-27 | 95 |
| [dkorobtsov/pitch-deck](https://github.com/dkorobtsov/pitch-deck) | `slow` | 2026-03-22 | 8 |
| [ebrahimpichka/DeepRL-trade](https://github.com/ebrahimpichka/DeepRL-trade) | `slow` | 2026-02-13 | 21 |
| [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | `slow` | 2026-03-23 | 4477 |
| [FlagOpen/RoboBrain2.5](https://github.com/FlagOpen/RoboBrain2.5) | `slow` | 2026-02-28 | 1126 |
| [fsaavedra0003/Agentic-AI-Trading-Bot-with-LLM-reasoning-sentiment-analysis](https://github.com/fsaavedra0003/Agentic-AI-Trading-Bot-with-LLM-reasoning-sentiment-analysis) | `slow` | 2026-03-10 | 8 |
| [geekan/MetaGPT](https://github.com/geekan/MetaGPT) | `slow` | 2026-01-21 | 69860 |
| [HappyHackingSpace/awesome-hackathon](https://github.com/HappyHackingSpace/awesome-hackathon) | `slow` | 2026-05-06 | 84 |
| [jmfernandes/robin_stocks](https://github.com/jmfernandes/robin_stocks) | `slow` | 2026-02-11 | 2110 |
| [LQF-dev/Zero-code](https://github.com/LQF-dev/Zero-code) | `slow` | 2026-05-09 | 68 |
| [Lumiwealth/lumiwealth-tradier](https://github.com/Lumiwealth/lumiwealth-tradier) | `slow` | 2026-01-05 | 16 |
| [marcozanetti-dev/intraday-mean-reversion-costs-aware](https://github.com/marcozanetti-dev/intraday-mean-reversion-costs-aware) | `slow` | 2026-01-05 | 0 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | `slow` | 2026-04-15 | 60460 |
| [microsoft/lets-learn-mcp-python](https://github.com/microsoft/lets-learn-mcp-python) | `slow` | 2025-09-24 | 1064 |
| [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua) | `slow` | 2026-04-08 | 6571 |
| [mlabouardy/komiser](https://github.com/mlabouardy/komiser) | `slow` | 2026-04-12 | 4138 |
| [MrDecryptDecipher/Sentinel](https://github.com/MrDecryptDecipher/Sentinel) | `slow` | 2025-12-07 | 1 |
| [padmarajkore/Ai-crypto-trading-system](https://github.com/padmarajkore/Ai-crypto-trading-system) | `slow` | 2026-01-18 | 2 |
| [passiv/snaptrade-react](https://github.com/passiv/snaptrade-react) | `slow` | 2025-11-17 | 5 |
| [phildougherty/infracost_mcp](https://github.com/phildougherty/infracost_mcp) | `slow` | 2025-11-07 | 2 |
| [qiskit-community/qiskit-finance](https://github.com/qiskit-community/qiskit-finance) | `slow` | 2025-12-12 | 326 |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | `slow` | 2025-11-09 | 3161 |
| [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) | `slow` | 2026-04-11 | 477 |
| [rpng/open_vins](https://github.com/rpng/open_vins) | `slow` | 2025-11-30 | 3045 |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | `slow` | 2026-03-30 | 2302 |
| [tastytrade/tastytrade-api-js](https://github.com/tastytrade/tastytrade-api-js) | `slow` | 2026-05-17 | 107 |
| [thammo4/uvatradier](https://github.com/thammo4/uvatradier) | `slow` | 2026-04-18 | 29 |
| [TradingGoose/TradingGoose.github.io](https://github.com/TradingGoose/TradingGoose.github.io) | `slow` | 2026-04-22 | 78 |
| [upstash/rag-chat](https://github.com/upstash/rag-chat) | `slow` | 2025-12-15 | 259 |
| [upstash/vector-js](https://github.com/upstash/vector-js) | `slow` | 2026-03-09 | 70 |
| [VarunRathore137/The-Hybrid-Quantum-Portfolio-Optimizer](https://github.com/VarunRathore137/The-Hybrid-Quantum-Portfolio-Optimizer) | `slow` | 2026-01-21 | 1 |
| [VictorVVedtion/trading-skills](https://github.com/VictorVVedtion/trading-skills) | `slow` | 2026-04-07 | 15 |
| [wangcangshu/codex-desktop-thread-rescue](https://github.com/wangcangshu/codex-desktop-thread-rescue) | `slow` | 2026-05-04 | 15 |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | `active` | 2026-08-14 | 87841 |
| [agno-agi/agno](https://github.com/agno-agi/agno) | `active` | 2026-08-17 | 41737 |
| [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | `active` | 2026-08-02 | 21100 |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | `active` | 2026-07-13 | 16027 |
| [ai4finance-foundation/finrobot](https://github.com/ai4finance-foundation/finrobot) | `active` | 2026-07-27 | 7793 |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | `active` | 2026-08-17 | 24536 |
| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | `active` | 2026-08-10 | 918 |
| [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) | `active` | 2026-08-14 | 1462 |
| [anchore/syft](https://github.com/anchore/syft) | `active` | 2026-08-14 | 9408 |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | `active` | 2026-08-14 | 37440 |
| [AsyncAlgoTrading/aat](https://github.com/AsyncAlgoTrading/aat) | `active` | 2026-07-27 | 828 |
| [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp) | `active` | 2026-08-07 | 3988 |
| [aws/amazon-braket-sdk-python](https://github.com/aws/amazon-braket-sdk-python) | `active` | 2026-08-13 | 373 |
| [awslabs/mcp](https://github.com/awslabs/mcp) | `active` | 2026-08-14 | 9609 |
| [BIKASH1002/QML-Stock-Predictor](https://github.com/BIKASH1002/QML-Stock-Predictor) | `active` | 2026-06-25 | 8 |
| [borglab/gtsam](https://github.com/borglab/gtsam) | `active` | 2026-08-17 | 3635 |
| [bradygaster/Aspiregregator](https://github.com/bradygaster/Aspiregregator) | `active` | 2026-08-08 | 1 |
| [bradygaster/squad](https://github.com/bradygaster/squad) | `active` | 2026-08-16 | 3100 |
| [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) | `active` | 2026-08-13 | 8944 |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | `active` | 2026-08-16 | 109469 |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | `active` | 2026-07-27 | 6136 |
| [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup) | `active` | 2026-08-01 | 2587 |
| [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | `active` | 2026-08-17 | 50596 |
| [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | `active` | 2026-08-14 | 1034 |
| [cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian) | `active` | 2026-08-14 | 6046 |
| [cloudquery/cloudquery](https://github.com/cloudquery/cloudquery) | `active` | 2026-08-17 | 6481 |
| [coinbase/coinbase-advanced-py](https://github.com/coinbase/coinbase-advanced-py) | `active` | 2026-06-19 | 355 |
| [colmap/colmap](https://github.com/colmap/colmap) | `active` | 2026-08-14 | 12494 |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | `active` | 2026-08-13 | 17629 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | `active` | 2026-08-17 | 57186 |
| [DhruvaBansal00/robin_stocks_v2](https://github.com/DhruvaBansal00/robin_stocks_v2) | `active` | 2026-08-08 | 7 |
| [dwavesystems/dwave-ocean-sdk](https://github.com/dwavesystems/dwave-ocean-sdk) | `active` | 2026-08-10 | 536 |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | `active` | 2026-08-14 | 13680 |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | `active` | 2026-08-06 | 4365 |
| [expo/examples](https://github.com/expo/examples) | `active` | 2026-07-28 | 3706 |
| [expo/expo](https://github.com/expo/expo) | `active` | 2026-08-17 | 51644 |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | `active` | 2026-08-07 | 3650 |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | `active` | 2026-05-19 | 14236 |
| [ferdousbhai/tasty-agent](https://github.com/ferdousbhai/tasty-agent) | `active` | 2026-08-14 | 83 |
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | `active` | 2026-08-17 | 53362 |
| [georgezouq/awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | `active` | 2026-08-04 | 6406 |
| [getomnico/omni](https://github.com/getomnico/omni) | `active` | 2026-08-09 | 758 |
| [getzep/graphiti](https://github.com/getzep/graphiti) | `active` | 2026-08-16 | 29987 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | `active` | 2026-08-17 | 124269 |
| [github/copilot-cli](https://github.com/github/copilot-cli) | `active` | 2026-08-14 | 11098 |
| [github/copilot-sdk](https://github.com/github/copilot-sdk) | `active` | 2026-08-17 | 10413 |
| [github/docs](https://github.com/github/docs) | `active` | 2026-08-14 | 20680 |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | `active` | 2026-08-14 | 32295 |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | `active` | 2026-07-29 | 28763 |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | `active` | 2026-08-17 | 106533 |
| [google/osv-scanner](https://github.com/google/osv-scanner) | `active` | 2026-08-17 | 10842 |
| [guorunjie/codex-relay-baton-guardian](https://github.com/guorunjie/codex-relay-baton-guardian) | `active` | 2026-06-11 | 1 |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | `active` | 2026-08-17 | 66566 |
| [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) | `active` | 2026-06-11 | 21432 |
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | `active` | 2026-08-17 | 38914 |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | `active` | 2026-08-16 | 31056 |
| [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | `active` | 2026-08-16 | 914 |
| [huahuadeliaoliao/codex-session-compact-collapse](https://github.com/huahuadeliaoliao/codex-session-compact-collapse) | `active` | 2026-07-01 | 1 |
| [ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async) | `active` | 2026-07-15 | 1714 |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | `active` | 2026-08-17 | 88633 |
| [infracost/agent-skills](https://github.com/infracost/agent-skills) | `active` | 2026-08-06 | 12 |
| [infracost/infracost](https://github.com/infracost/infracost) | `active` | 2026-08-11 | 12459 |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | `active` | 2026-08-17 | 13888 |
| [jasonwilbur/cloud-cost-mcp](https://github.com/jasonwilbur/cloud-cost-mcp) | `active` | 2026-06-03 | 5 |
| [Jesse-ai/jesse](https://github.com/Jesse-ai/jesse) | `active` | 2026-08-16 | 8335 |
| [jpmorganchase/QOKit](https://github.com/jpmorganchase/QOKit) | `active` | 2026-06-17 | 100 |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | `active` | 2026-08-05 | 8859 |
| [koide3/glim](https://github.com/koide3/glim) | `active` | 2026-08-14 | 1744 |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | `active` | 2026-08-17 | 144365 |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | `active` | 2026-08-10 | 12626 |
| [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | `active` | 2026-08-17 | 153345 |
| [langgenius/dify](https://github.com/langgenius/dify) | `active` | 2026-08-17 | 152655 |
| [lightonai/pylate](https://github.com/lightonai/pylate) | `active` | 2026-07-23 | 878 |
| [lobehub/lobe-chat](https://github.com/lobehub/lobe-chat) | `active` | 2026-08-17 | 81759 |
| [Lumiwealth/lumibot](https://github.com/Lumiwealth/lumibot) | `active` | 2026-08-13 | 1939 |
| [marp-team/marpit](https://github.com/marp-team/marpit) | `active` | 2026-08-03 | 1364 |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | `active` | 2026-08-15 | 63407 |
| [microsoft/agents](https://github.com/microsoft/agents) | `active` | 2026-08-13 | 1039 |
| [microsoft/Agents-for-net](https://github.com/microsoft/Agents-for-net) | `active` | 2026-08-14 | 175 |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | `active` | 2026-07-29 | 72366 |
| [microsoft/mcp](https://github.com/microsoft/mcp) | `active` | 2026-08-14 | 3575 |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | `active` | 2026-08-12 | 36190 |
| [microsoft/qsharp](https://github.com/microsoft/qsharp) | `active` | 2026-08-16 | 992 |
| [microsoftdocs/mcp](https://github.com/microsoftdocs/mcp) | `active` | 2026-08-12 | 1839 |
| [mindsdb/mindsdb](https://github.com/mindsdb/mindsdb) | `active` | 2026-08-13 | 39591 |
| [MingyuJ666/Stockagent](https://github.com/MingyuJ666/Stockagent) | `active` | 2026-06-16 | 692 |
| [mit-han-lab/torchquantum](https://github.com/mit-han-lab/torchquantum) | `active` | 2026-07-06 | 1660 |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | `active` | 2026-08-17 | 1124 |
| [mnemox-ai/tradememory-protocol](https://github.com/mnemox-ai/tradememory-protocol) | `active` | 2026-08-11 | 1410 |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | `active` | 2026-08-17 | 10676 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | `active` | 2026-08-16 | 24027 |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | `active` | 2026-08-10 | 89613 |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | `active` | 2026-08-17 | 13187 |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | `active` | 2026-08-16 | 3541 |
| [mudler/LocalAI](https://github.com/mudler/LocalAI) | `active` | 2026-08-17 | 48517 |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | `active` | 2026-08-17 | 25629 |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | `active` | 2026-08-15 | 5544 |
| [nozomi-koborinai/gcp-cost-mcp-server](https://github.com/nozomi-koborinai/gcp-cost-mcp-server) | `active` | 2026-07-19 | 22 |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | `active` | 2026-07-03 | 1268 |
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | `active` | 2026-08-16 | 11530 |
| [NVIDIA/cuda-quantum](https://github.com/NVIDIA/cuda-quantum) | `active` | 2026-08-17 | 1112 |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | `active` | 2026-08-14 | 8831 |
| [NVIDIA/skills](https://github.com/NVIDIA/skills) | `active` | 2026-08-17 | 2976 |
| [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) | `active` | 2026-06-02 | 4313 |
| [OfficeDev/microsoft-365-agents-toolkit](https://github.com/OfficeDev/microsoft-365-agents-toolkit) | `active` | 2026-08-17 | 771 |
| [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) | `active` | 2026-08-17 | 8948 |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | `active` | 2026-08-16 | 31627 |
| [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | `active` | 2026-08-16 | 487 |
| [openai/codex](https://github.com/openai/codex) | `active` | 2026-08-17 | 106358 |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | `active` | 2026-07-30 | 71951 |
| [opencost/opencost](https://github.com/opencost/opencost) | `active` | 2026-08-11 | 6680 |
| [opencost/opencost-helm-chart](https://github.com/opencost/opencost-helm-chart) | `active` | 2026-08-05 | 108 |
| [opengrep/opengrep](https://github.com/opengrep/opengrep) | `active` | 2026-08-14 | 2956 |
| [OptimNow/cloud-finops-skills](https://github.com/OptimNow/cloud-finops-skills) | `active` | 2026-08-16 | 46 |
| [OptimNow/finops-mcp-resources](https://github.com/OptimNow/finops-mcp-resources) | `active` | 2026-08-16 | 26 |
| [ossf/scorecard](https://github.com/ossf/scorecard) | `active` | 2026-08-15 | 5639 |
| [paradedb/paradedb](https://github.com/paradedb/paradedb) | `active` | 2026-08-17 | 9164 |
| [passiv/snaptrade-cli](https://github.com/passiv/snaptrade-cli) | `active` | 2026-08-04 | 29 |
| [passiv/snaptrade-sdks](https://github.com/passiv/snaptrade-sdks) | `active` | 2026-08-13 | 53 |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | `active` | 2026-08-17 | 62446 |
| [PennyLaneAI/pennylane](https://github.com/PennyLaneAI/pennylane) | `active` | 2026-08-17 | 3418 |
| [PennyLaneAI/pennylane-qiskit](https://github.com/PennyLaneAI/pennylane-qiskit) | `active` | 2026-08-13 | 239 |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | `active` | 2026-06-16 | 13335 |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | `active` | 2026-08-13 | 9861 |
| [pmorissette/bt](https://github.com/pmorissette/bt) | `active` | 2026-08-07 | 2962 |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | `active` | 2026-08-03 | 92459 |
| [qiskit-community/qiskit-machine-learning](https://github.com/qiskit-community/qiskit-machine-learning) | `active` | 2026-08-10 | 1091 |
| [Qiskit/qiskit](https://github.com/Qiskit/qiskit) | `active` | 2026-08-17 | 7712 |
| [qmyhd/LLM-portfolio-project](https://github.com/qmyhd/LLM-portfolio-project) | `active` | 2026-07-22 | 2 |
| [qosf/awesome-quantum-software](https://github.com/qosf/awesome-quantum-software) | `active` | 2026-08-15 | 2377 |
| [quantconnect/Lean](https://github.com/quantconnect/Lean) | `active` | 2026-08-14 | 21243 |
| [quantumlib/Cirq](https://github.com/quantumlib/Cirq) | `active` | 2026-08-14 | 5049 |
| [QwenLM/Qwen3.6](https://github.com/QwenLM/Qwen3.6) | `active` | 2026-08-17 | 3798 |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | `active` | 2026-08-13 | 24999 |
| [rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all) | `active` | 2026-08-14 | 1857 |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | `active` | 2026-08-15 | 586 |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | `active` | 2026-08-16 | 11312 |
| [RezaSoleymanifar/neuralHFT](https://github.com/RezaSoleymanifar/neuralHFT) | `active` | 2026-08-06 | 40 |
| [rhettre/coinbase-advancedtrade-python](https://github.com/rhettre/coinbase-advancedtrade-python) | `active` | 2026-06-05 | 122 |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | `active` | 2026-08-17 | 27092 |
| [roninoss/create-expo-stack](https://github.com/roninoss/create-expo-stack) | `active` | 2026-07-08 | 2576 |
| [runagent-dev/runagent](https://github.com/runagent-dev/runagent) | `active` | 2026-06-27 | 481 |
| [RyanWeb31110/codex-thread-handoff](https://github.com/RyanWeb31110/codex-thread-handoff) | `active` | 2026-06-10 | 0 |
| [Sapience-AI/openclaw-middleware-suite](https://github.com/Sapience-AI/openclaw-middleware-suite) | `active` | 2026-08-11 | 10 |
| [satoshiman/rag-cli](https://github.com/satoshiman/rag-cli) | `active` | 2026-05-22 | 2 |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | `active` | 2026-08-17 | 16245 |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | `active` | 2026-08-17 | 31937 |
| [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | `active` | 2026-08-17 | 186641 |
| [sigstore/cosign](https://github.com/sigstore/cosign) | `active` | 2026-08-14 | 6215 |
| [simple10/agents-observe](https://github.com/simple10/agents-observe) | `active` | 2026-07-22 | 649 |
| [siropkin/robinhood-ai-trading-bot](https://github.com/siropkin/robinhood-ai-trading-bot) | `active` | 2026-06-30 | 121 |
| [slidevjs/slidev](https://github.com/slidevjs/slidev) | `active` | 2026-08-14 | 48111 |
| [snyk/cli](https://github.com/snyk/cli) | `active` | 2026-08-17 | 5641 |
| [soolaugust/0CompactMem](https://github.com/soolaugust/0CompactMem) | `active` | 2026-07-14 | 4 |
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | `active` | 2026-08-14 | 1233 |
| [tastyware/tastytrade](https://github.com/tastyware/tastytrade) | `active` | 2026-08-07 | 255 |
| [tastyware/tastytrade-cli](https://github.com/tastyware/tastytrade-cli) | `active` | 2026-08-10 | 77 |
| [tauricresearch/tradingagents](https://github.com/tauricresearch/tradingagents) | `active` | 2026-07-18 | 98549 |
| [tensorflow/quantum](https://github.com/tensorflow/quantum) | `active` | 2026-08-05 | 2180 |
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | `active` | 2026-08-17 | 90927 |
| [ToolJet/ToolJet](https://github.com/ToolJet/ToolJet) | `active` | 2026-08-17 | 40228 |
| [TradingAgents-AI/TradingAgents](https://github.com/TradingAgents-AI/TradingAgents) | `active` | 2026-07-18 | 98549 |
| [tradingstrategy-ai/getting-started](https://github.com/tradingstrategy-ai/getting-started) | `active` | 2026-08-12 | 243 |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | `active` | 2026-08-16 | 27488 |
| [turbot/steampipe](https://github.com/turbot/steampipe) | `active` | 2026-08-10 | 7915 |
| [tylerebowers/Schwabdev](https://github.com/tylerebowers/Schwabdev) | `active` | 2026-08-11 | 849 |
| [unitaryfund/mitiq](https://github.com/unitaryfund/mitiq) | `active` | 2026-08-07 | 441 |
| [upstash/context7](https://github.com/upstash/context7) | `active` | 2026-08-16 | 60854 |
| [vespa-engine/vespa](https://github.com/vespa-engine/vespa) | `active` | 2026-08-17 | 7052 |
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | `active` | 2026-08-17 | 3687 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | `active` | 2026-08-17 | 89221 |
| [vnpy/vnpy](https://github.com/vnpy/vnpy) | `active` | 2026-08-10 | 44562 |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | `active` | 2026-08-16 | 30410 |
| [wshobson/maverick-mcp](https://github.com/wshobson/maverick-mcp) | `active` | 2026-08-16 | 644 |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | `active` | 2026-07-25 | 420 |
| [YeQing17-2026/OmniAgent](https://github.com/YeQing17-2026/OmniAgent) | `active` | 2026-07-27 | 2543 |
| [Yuchen20/Context-Crumb](https://github.com/Yuchen20/Context-Crumb) | `active` | 2026-06-03 | 1 |
| [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | `active` | 2026-08-17 | 3588 |
| [zai-org/GLM-5](https://github.com/zai-org/GLM-5) | `active` | 2026-08-11 | 6980 |
| [zzallirog/weighted-compact](https://github.com/zzallirog/weighted-compact) | `active` | 2026-06-10 | 4 |

<!-- FRESHNESS:END -->


## Removed — unmaintained or missing

Dropped from the catalog on 2026-08-05 by `scripts/check_freshness.py`.
A repo is removed at 18+ months without a commit, or when it 404s.

| Repo | Status | Last push | Replacement |
| --- | --- | --- | --- |
| `Acciorocketships/algo-trader` | `unmaintained` | 2024-06-21 | — |
| `Albert-Z-Guo/Deep-Reinforcement-Stock-Trading` | `unmaintained` | 2024-11-06 | — |
| `alejomonbar/Quantum-Counselor-for-Portfolio-Investment` | `unmaintained` | 2022-06-02 | — |
| `alpacahq/alpaca-trade-api-python` | `unmaintained` | 2024-01-12 | [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) |
| `bradygaster/Aspire.Hosting.Facepunch.Rust` | `unmaintained` | 2024-11-13 | — |
| `bradygaster/ASPNETCoreWithYarpOnAzureContainerApps` | `unmaintained` | 2022-01-05 | — |
| `bradygaster/AugmentR` | `unmaintained` | 2024-03-12 | — |
| `ChiraagNadig/Quantum-ML-Research` | `unmaintained` | 2025-01-11 | — |
| `DarkStarQuantumLab/Qauntum-trading-a-disturbance-in-the-force-of-supply-and-demand` | `unmaintained` | 2023-09-03 | — |
| `entropicalabs/openqaoa` | `unmaintained` | 2024-07-10 | — |
| `erdewit/ib_insync` | `unmaintained` | 2024-03-14 | [ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async) |
| `gbeced/pyalgotrade` | `unmaintained` | 2023-03-05 | — |
| `hakantekgul/ML_Automated_Trading_Robinhood` | `unmaintained` | 2020-05-05 | — |
| `huseinzol05/Stock-Prediction-Models` | `unmaintained` | 2021-01-05 | — |
| `itsjafer/schwab-api` | `unmaintained` | 2024-07-20 | — |
| `LIU-HONGYANG-GZU/Live_Trade_Bench` | `missing` | never | — |
| `matplotlib/mplfinance` | `unmaintained` | 2024-04-02 | — |
| `mementum/backtrader` | `unmaintained` | 2023-04-19 | — |
| `MonitSharma/Quantum-Finance-and-Numerical-Methods` | `unmaintained` | 2023-07-03 | — |
| `PaddlePaddle/Quantum` | `unmaintained` | 2023-04-24 | — |
| `pushshift/tradier` | `unmaintained` | 2017-10-03 | — |
| `PythonForForex/ib_insync-guide-interactive-brokers` | `unmaintained` | 2022-04-11 | — |
| `qBraid/nyc-haq-qbraid` | `unmaintained` | 2024-09-21 | — |
| `QuantaScriptor/Quantum-Based-Portfolio-Diversification-QBPD` | `unmaintained` | 2024-09-05 | — |
| `robinhood-unofficial/pyrh` | `unmaintained` | 2024-03-04 | — |
| `sanko/robinhood` | `unmaintained` | 2024-05-08 | — |
| `sargun/tradier` | `unmaintained` | 2020-08-05 | — |
| `System-R-AI/systemr-python` | `missing` | never | — |
| `tejaslinge/Alpaca-ROC-Trading-Bot` | `unmaintained` | 2022-04-29 | — |
| `tejaslinge/Alpaca-StochRSI-EMA-Trading-Bot` | `unmaintained` | 2022-03-10 | — |
| `timpalpant/go-tradier` | `unmaintained` | 2021-07-04 | — |
| `varunon9/rag-langchain-nodejs` | `unmaintained` | 2024-08-24 | — |
