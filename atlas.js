'use strict';

const ATLAS_META = Object.freeze({
  release: 'V7',
  componentCount: 52,
  laneCount: 16,
  canvasCount: 12,
  routeCount: 36
});

const SVG_NS = 'http://www.w3.org/2000/svg';
const KIND_COLORS = {
  instruction: '#ff7a3d',
  capability: '#52d9ff',
  knowledge: '#c5a6ff',
  compute: '#79e7b7',
  control: '#f5d66c',
  delivery: '#ff777d'
};

const LANE_DEFINITIONS = [
  { id: 'intake', name: 'Intake', kind: 'instruction' },
  { id: 'surfaces', name: 'Client surfaces', kind: 'capability' },
  { id: 'identity', name: 'Identity', kind: 'control' },
  { id: 'instructions', name: 'Instruction layer', kind: 'instruction' },
  { id: 'skills', name: 'Skills', kind: 'capability' },
  { id: 'connectors', name: 'Connectors', kind: 'capability' },
  { id: 'knowledge', name: 'Knowledge', kind: 'knowledge' },
  { id: 'retrieval', name: 'Retrieval', kind: 'knowledge' },
  { id: 'validation', name: 'Validation', kind: 'control' },
  { id: 'routing', name: 'Routing', kind: 'control' },
  { id: 'local', name: 'Local models', kind: 'compute' },
  { id: 'hosted', name: 'Hosted models', kind: 'compute' },
  { id: 'hybrid', name: 'Hybrid control', kind: 'control' },
  { id: 'observe', name: 'Observability', kind: 'knowledge' },
  { id: 'governance', name: 'Governance', kind: 'control' },
  { id: 'delivery', name: 'Delivery', kind: 'delivery' }
];

const COMPONENT_DEFINITIONS = [
  { id: 'task', name: 'Task intake', lane: 'intake', x: 245, kind: 'instruction', detail: 'Normalizes the request and starts the system trace.', cmd: { windows: 'python scripts/catalog_guardian.py --help', macos: 'python3 scripts/catalog_guardian.py --help', linux: 'python3 scripts/catalog_guardian.py --help' } },
  { id: 'scope', name: 'Scope resolver', lane: 'intake', x: 610, kind: 'control', detail: 'Identifies the smallest safe set of resources for the task.' },
  { id: 'intent', name: 'Intent signal', lane: 'intake', x: 975, kind: 'instruction', detail: 'Classifies the desired outcome and interaction mode.' },
  { id: 'codex', name: 'Codex', lane: 'surfaces', x: 220, kind: 'capability', detail: 'Repository aware coding and system work surface.' },
  { id: 'copilot', name: 'Copilot', lane: 'surfaces', x: 505, kind: 'capability', detail: 'Native GitHub assistant surface.' },
  { id: 'claude', name: 'Claude', lane: 'surfaces', x: 790, kind: 'capability', detail: 'General agent and coding surface.' },
  { id: 'gemini', name: 'Gemini', lane: 'surfaces', x: 1075, kind: 'capability', detail: 'Multimodal and hosted model surface.' },
  { id: 'clone', name: 'Clone client', lane: 'surfaces', x: 1360, kind: 'capability', detail: 'Any compatible local or hosted client adapter.' },
  { id: 'workspace', name: 'Workspace trust', lane: 'identity', x: 300, kind: 'control', detail: 'Binds access to the active repository and workspace.' },
  { id: 'profile', name: 'User profile', lane: 'identity', x: 720, kind: 'control', detail: 'Applies local preferences without exposing secrets.' },
  { id: 'policy', name: 'Access policy', lane: 'identity', x: 1140, kind: 'control', detail: 'Enforces tool and filesystem permission boundaries.' },
  { id: 'agents', name: 'Agent contract', lane: 'instructions', x: 250, kind: 'instruction', detail: 'Loads repository behavior and safety rules.' },
  { id: 'setup', name: 'Setup guide', lane: 'instructions', x: 600, kind: 'instruction', detail: 'Routes the user toward client specific setup.' },
  { id: 'prompt', name: 'Prompt layer', lane: 'instructions', x: 950, kind: 'instruction', detail: 'Shapes task context and instruction priority.' },
  { id: 'budget', name: 'Token budget', lane: 'instructions', x: 1300, kind: 'instruction', detail: 'Keeps context and hosted model spend bounded.' },
  { id: 'skills', name: 'Skill registry', lane: 'skills', x: 260, kind: 'capability', detail: 'Selects task specific instruction packages.' },
  { id: 'plugins', name: 'Plugin bridge', lane: 'skills', x: 650, kind: 'capability', detail: 'Provides packaged skills, tools, and app connections.' },
  { id: 'skilltests', name: 'Skill quality', lane: 'skills', x: 1040, kind: 'control', detail: 'Checks scope, clarity, and expected behavior.' },
  { id: 'githubmcp', name: 'GitHub MCP', lane: 'connectors', x: 230, kind: 'capability', detail: 'Connects repository and issue workflows.' },
  { id: 'context7', name: 'Context lookup', lane: 'connectors', x: 540, kind: 'capability', detail: 'Retrieves current technical documentation.' },
  { id: 'browser', name: 'Browser control', lane: 'connectors', x: 850, kind: 'capability', detail: 'Tests and inspects interactive web surfaces.' },
  { id: 'apphub', name: 'App connector hub', lane: 'connectors', x: 1160, kind: 'capability', detail: 'Routes account backed tools with scoped access.' },
  { id: 'catalog', name: 'Repo catalog', lane: 'knowledge', x: 250, kind: 'knowledge', detail: 'Indexes vetted resources by task lane.' },
  { id: 'docs', name: 'Docs index', lane: 'knowledge', x: 610, kind: 'knowledge', detail: 'Finds canonical repository guidance.' },
  { id: 'history', name: 'Decision history', lane: 'knowledge', x: 970, kind: 'knowledge', detail: 'Keeps prior design and architecture context accessible.' },
  { id: 'chunks', name: 'Context chunks', lane: 'retrieval', x: 260, kind: 'knowledge', detail: 'Retrieves only the relevant source fragments.' },
  { id: 'vector', name: 'Vector cache', lane: 'retrieval', x: 610, kind: 'knowledge', detail: 'Stores reusable semantic retrieval signals.' },
  { id: 'rerank', name: 'Evidence reranker', lane: 'retrieval', x: 960, kind: 'knowledge', detail: 'Prioritizes the most relevant verified context.' },
  { id: 'validators', name: 'Static validators', lane: 'validation', x: 235, kind: 'control', detail: 'Runs deterministic policy and syntax checks.' },
  { id: 'schema', name: 'Schema check', lane: 'validation', x: 555, kind: 'control', detail: 'Verifies public and internal data contracts.' },
  { id: 'quality', name: 'Quality gate', lane: 'validation', x: 875, kind: 'control', detail: 'Combines tests, review, and experiential checks.' },
  { id: 'privacy', name: 'Privacy gate', lane: 'validation', x: 1195, kind: 'control', detail: 'Blocks repository level data from public artifacts.' },
  { id: 'router', name: 'Hybrid router', lane: 'routing', x: 310, kind: 'control', detail: 'Selects local, hosted, or split execution.' },
  { id: 'routepolicy', name: 'Route policy', lane: 'routing', x: 720, kind: 'control', detail: 'Balances quality, latency, privacy, and cost.' },
  { id: 'fallback', name: 'Fallback graph', lane: 'routing', x: 1130, kind: 'control', detail: 'Defines recovery when a model or tool is unavailable.' },
  { id: 'tiny', name: 'Tiny local', lane: 'local', x: 230, kind: 'compute', detail: 'Fast extraction and classification on constrained hardware.' },
  { id: 'small', name: 'Small local', lane: 'local', x: 530, kind: 'compute', detail: 'Everyday summaries, edits, and structured work.' },
  { id: 'mid', name: 'Mid local', lane: 'local', x: 830, kind: 'compute', detail: 'Practical coding and deeper local reasoning.' },
  { id: 'large', name: 'Large local', lane: 'local', x: 1130, kind: 'compute', detail: 'High capability local work on strong hardware.' },
  { id: 'hostfast', name: 'Hosted fast', lane: 'hosted', x: 330, kind: 'compute', detail: 'Low latency hosted completion for burst demand.' },
  { id: 'hostbalanced', name: 'Hosted balanced', lane: 'hosted', x: 720, kind: 'compute', detail: 'General hosted reasoning with balanced cost.' },
  { id: 'hostdeep', name: 'Hosted deep', lane: 'hosted', x: 1110, kind: 'compute', detail: 'High depth reasoning for complex, verified work.' },
  { id: 'localfirst', name: 'Local first', lane: 'hybrid', x: 245, kind: 'control', detail: 'Keeps eligible tasks on the user machine.' },
  { id: 'splitwork', name: 'Split workload', lane: 'hybrid', x: 565, kind: 'control', detail: 'Divides retrieval, generation, and validation.' },
  { id: 'verifyroute', name: 'Verify then lift', lane: 'hybrid', x: 885, kind: 'control', detail: 'Escalates only after local validation finds uncertainty.' },
  { id: 'budgetroute', name: 'Budget governor', lane: 'hybrid', x: 1205, kind: 'control', detail: 'Limits hosted calls to the highest value steps.' },
  { id: 'telemetry', name: 'Route telemetry', lane: 'observe', x: 285, kind: 'knowledge', detail: 'Records aggregate path performance.' },
  { id: 'costmeter', name: 'Cost meter', lane: 'observe', x: 695, kind: 'knowledge', detail: 'Tracks model and tool cost signals.' },
  { id: 'trace', name: 'Trace explorer', lane: 'observe', x: 1105, kind: 'knowledge', detail: 'Makes the complete route inspectable.' },
  { id: 'guardian', name: 'Catalog guardian', lane: 'governance', x: 280, kind: 'control', detail: 'Applies lifecycle and maintenance policy.' },
  { id: 'security', name: 'Security scan', lane: 'governance', x: 690, kind: 'control', detail: 'Runs safe static intake and repository checks.' },
  { id: 'release', name: 'Public delivery', lane: 'delivery', x: 480, kind: 'delivery', detail: 'Builds the privacy safe site and release artifact.', cmd: { windows: 'python scripts/build_public_site.py', macos: 'python3 scripts/build_public_site.py', linux: 'python3 scripts/build_public_site.py' } }
];

const CANVAS_DEFINITIONS = [
  { id: 'atlas', name: 'Full Atlas', code: 'C01', tone: '#ff7a3d', lanes: LANE_DEFINITIONS.map(function (lane) { return lane.id; }), summary: 'Complete topology' },
  { id: 'launch', name: 'Launchpad', code: 'C02', tone: '#52d9ff', lanes: ['intake', 'surfaces', 'identity', 'instructions'], summary: 'Task to contract' },
  { id: 'identity', name: 'Identity Mesh', code: 'C03', tone: '#f5d66c', lanes: ['surfaces', 'identity', 'governance'], summary: 'Trust and access' },
  { id: 'capability', name: 'Capability Grid', code: 'C04', tone: '#52d9ff', lanes: ['instructions', 'skills', 'connectors'], summary: 'Skills and tools' },
  { id: 'knowledge', name: 'Knowledge Flow', code: 'C05', tone: '#c5a6ff', lanes: ['knowledge', 'retrieval', 'validation'], summary: 'Evidence path' },
  { id: 'validation', name: 'Validation Gate', code: 'C06', tone: '#f5d66c', lanes: ['retrieval', 'validation', 'governance'], summary: 'Quality and privacy' },
  { id: 'local', name: 'Local Compute', code: 'C07', tone: '#79e7b7', lanes: ['routing', 'local', 'hybrid', 'observe'], summary: 'Private execution' },
  { id: 'hosted', name: 'Hosted Compute', code: 'C08', tone: '#ffaf7d', lanes: ['routing', 'hosted', 'hybrid', 'observe'], summary: 'Elastic reasoning' },
  { id: 'hybrid', name: 'Hybrid Fabric', code: 'C09', tone: '#52d9ff', lanes: ['validation', 'routing', 'local', 'hosted', 'hybrid', 'observe'], summary: 'Thirty six routes' },
  { id: 'observe', name: 'Observability', code: 'C10', tone: '#c5a6ff', lanes: ['routing', 'hybrid', 'observe'], summary: 'Trace and cost' },
  { id: 'governance', name: 'Governance', code: 'C11', tone: '#f5d66c', lanes: ['identity', 'validation', 'observe', 'governance'], summary: 'Policy boundary' },
  { id: 'delivery', name: 'Delivery', code: 'C12', tone: '#ff777d', lanes: ['validation', 'observe', 'governance', 'delivery'], summary: 'Verified release' }
];

function route(id, name, category, color, nodes, rule, latency, cost, privacy) {
  return { id: id, name: name, category: category, color: color, nodes: nodes, rule: rule, latency: latency, cost: cost, privacy: privacy };
}

const ROUTE_DEFINITIONS = [
  route('cost-01', 'Budget scout', 'Cost', '#79e7b7', ['task', 'router', 'tiny', 'quality', 'release'], 'Use tiny local inference for classification and publish only after validation.', 'Fast', 'Lowest', 'Local'),
  route('cost-02', 'Lean drafting', 'Cost', '#79e7b7', ['task', 'skills', 'router', 'small', 'quality', 'release'], 'Keep generation local and reserve hosted capacity for no steps.', 'Fast', 'Low', 'Local'),
  route('cost-03', 'Selective lift', 'Cost', '#79e7b7', ['task', 'router', 'small', 'verifyroute', 'hostfast', 'quality', 'release'], 'Escalate only the uncertain segment after a local first pass.', 'Medium', 'Low', 'Hybrid'),
  route('cost-04', 'Cache and answer', 'Cost', '#79e7b7', ['task', 'chunks', 'vector', 'router', 'small', 'release'], 'Favor cached evidence and a compact local model.', 'Fast', 'Lowest', 'Local'),
  route('cost-05', 'Night shift', 'Cost', '#79e7b7', ['task', 'budget', 'router', 'mid', 'costmeter', 'release'], 'Run a stronger local model under a strict budget governor.', 'Medium', 'Low', 'Local'),
  route('cost-06', 'Value ceiling', 'Cost', '#79e7b7', ['task', 'routepolicy', 'budgetroute', 'hostbalanced', 'costmeter', 'quality', 'release'], 'Allow hosted reasoning until the configured value ceiling is reached.', 'Medium', 'Guarded', 'Hybrid'),
  route('privacy-01', 'Air gap', 'Privacy', '#c5a6ff', ['task', 'workspace', 'policy', 'router', 'small', 'privacy', 'release'], 'Keep inputs, context, inference, and validation on the local machine.', 'Fast', 'Low', 'Maximum'),
  route('privacy-02', 'Local RAG', 'Privacy', '#c5a6ff', ['task', 'catalog', 'chunks', 'vector', 'mid', 'privacy', 'release'], 'Retrieve and generate locally with no hosted context transfer.', 'Medium', 'Low', 'Maximum'),
  route('privacy-03', 'Redacted lift', 'Privacy', '#c5a6ff', ['task', 'policy', 'privacy', 'splitwork', 'hostfast', 'quality', 'release'], 'Redact sensitive context before a narrow hosted call.', 'Medium', 'Guarded', 'High'),
  route('privacy-04', 'Metadata only', 'Privacy', '#c5a6ff', ['task', 'policy', 'localfirst', 'tiny', 'telemetry', 'release'], 'Publish aggregate route metadata while keeping content private.', 'Fast', 'Lowest', 'Maximum'),
  route('privacy-05', 'Verified boundary', 'Privacy', '#c5a6ff', ['task', 'security', 'privacy', 'router', 'mid', 'quality', 'release'], 'Require security and privacy checks before local execution.', 'Medium', 'Low', 'Maximum'),
  route('privacy-06', 'Private fallback', 'Privacy', '#c5a6ff', ['task', 'routepolicy', 'fallback', 'large', 'privacy', 'release'], 'Fall back to the strongest available local model, never to hosted.', 'Slow', 'Local', 'Maximum'),
  route('quality-01', 'Double check', 'Quality', '#ff7a3d', ['task', 'rerank', 'mid', 'quality', 'hostbalanced', 'quality', 'release'], 'Compare a local answer with a hosted review before release.', 'Medium', 'Medium', 'Hybrid'),
  route('quality-02', 'Deep review', 'Quality', '#ff7a3d', ['task', 'skills', 'hostdeep', 'validators', 'quality', 'release'], 'Use deep hosted reasoning and deterministic validators.', 'Slow', 'Higher', 'Hosted'),
  route('quality-03', 'Evidence first', 'Quality', '#ff7a3d', ['task', 'docs', 'chunks', 'rerank', 'hostbalanced', 'quality', 'release'], 'Ground the response in reranked repository evidence.', 'Medium', 'Medium', 'Hybrid'),
  route('quality-04', 'Three pass', 'Quality', '#ff7a3d', ['task', 'small', 'mid', 'hostdeep', 'quality', 'release'], 'Draft, refine, and audit across increasing model capability.', 'Slow', 'Higher', 'Hybrid'),
  route('quality-05', 'Schema locked', 'Quality', '#ff7a3d', ['task', 'prompt', 'schema', 'hostbalanced', 'schema', 'release'], 'Constrain generation with a schema before and after inference.', 'Medium', 'Medium', 'Hosted'),
  route('quality-06', 'Senior gate', 'Quality', '#ff7a3d', ['task', 'mid', 'verifyroute', 'hostdeep', 'validators', 'quality', 'release'], 'Escalate complex findings to deep review and require the full gate.', 'Slow', 'Higher', 'Hybrid'),
  route('latency-01', 'Instant local', 'Latency', '#52d9ff', ['task', 'router', 'tiny', 'release'], 'Take the shortest valid local route for simple transformations.', 'Instant', 'Lowest', 'Local'),
  route('latency-02', 'Fast hosted', 'Latency', '#52d9ff', ['task', 'router', 'hostfast', 'release'], 'Use elastic hosted capacity for rapid burst responses.', 'Instant', 'Low', 'Hosted'),
  route('latency-03', 'Parallel race', 'Latency', '#52d9ff', ['task', 'splitwork', 'small', 'hostfast', 'quality', 'release'], 'Run local and hosted candidates together, then keep the first valid result.', 'Fastest', 'Medium', 'Hybrid'),
  route('latency-04', 'Cached context', 'Latency', '#52d9ff', ['task', 'vector', 'rerank', 'small', 'release'], 'Skip broad discovery by using cached, reranked context.', 'Fast', 'Low', 'Local'),
  route('latency-05', 'Quick verify', 'Latency', '#52d9ff', ['task', 'hostfast', 'validators', 'release'], 'Pair a fast hosted completion with deterministic checks.', 'Fast', 'Low', 'Hosted'),
  route('latency-06', 'Adaptive sprint', 'Latency', '#52d9ff', ['task', 'routepolicy', 'tiny', 'verifyroute', 'hostfast', 'release'], 'Start tiny and lift immediately when confidence drops.', 'Fast', 'Guarded', 'Hybrid'),
  route('offline-01', 'Offline tiny', 'Offline', '#f5d66c', ['task', 'agents', 'skills', 'tiny', 'validators', 'release'], 'Complete small deterministic work with no network dependency.', 'Fast', 'Local', 'Maximum'),
  route('offline-02', 'Offline daily', 'Offline', '#f5d66c', ['task', 'catalog', 'chunks', 'small', 'quality', 'release'], 'Use local repository context and a daily driver model.', 'Medium', 'Local', 'Maximum'),
  route('offline-03', 'Offline code', 'Offline', '#f5d66c', ['task', 'docs', 'mid', 'validators', 'quality', 'release'], 'Run coding work locally with repository checks.', 'Medium', 'Local', 'Maximum'),
  route('offline-04', 'Offline deep', 'Offline', '#f5d66c', ['task', 'rerank', 'large', 'quality', 'release'], 'Use strong local hardware for deeper private reasoning.', 'Slow', 'Local', 'Maximum'),
  route('offline-05', 'Disconnected fallback', 'Offline', '#f5d66c', ['task', 'fallback', 'small', 'validators', 'release'], 'Detect network loss and choose the safe local fallback.', 'Fast', 'Local', 'Maximum'),
  route('offline-06', 'Portable kit', 'Offline', '#f5d66c', ['task', 'setup', 'localfirst', 'tiny', 'privacy', 'release'], 'Use the smallest portable stack for field work.', 'Fast', 'Local', 'Maximum'),
  route('resilience-01', 'Model failover', 'Resilience', '#ff777d', ['task', 'router', 'fallback', 'small', 'hostfast', 'quality', 'release'], 'Move between local and hosted models when one path fails.', 'Variable', 'Guarded', 'Hybrid'),
  route('resilience-02', 'Connector failover', 'Resilience', '#ff777d', ['task', 'apphub', 'fallback', 'catalog', 'router', 'release'], 'Recover from connector loss using repository native context.', 'Variable', 'Low', 'Hybrid'),
  route('resilience-03', 'Validation recovery', 'Resilience', '#ff777d', ['task', 'quality', 'verifyroute', 'hostdeep', 'quality', 'release'], 'Retry failed validation with a stronger reasoning path.', 'Slow', 'Higher', 'Hybrid'),
  route('resilience-04', 'Budget recovery', 'Resilience', '#ff777d', ['task', 'costmeter', 'budgetroute', 'small', 'quality', 'release'], 'Drop to local execution when the hosted budget is exhausted.', 'Medium', 'Low', 'Hybrid'),
  route('resilience-05', 'Privacy recovery', 'Resilience', '#ff777d', ['task', 'privacy', 'fallback', 'mid', 'privacy', 'release'], 'Stay local when a hosted boundary check fails.', 'Medium', 'Local', 'Maximum'),
  route('resilience-06', 'Full circuit', 'Resilience', '#ff777d', ['task', 'routepolicy', 'fallback', 'splitwork', 'hostbalanced', 'telemetry', 'guardian', 'release'], 'Trace every fallback and end at a governed release.', 'Variable', 'Guarded', 'Hybrid')
];

const BACKBONE_EDGES = [
  ['task', 'scope'], ['scope', 'intent'], ['intent', 'codex'], ['intent', 'copilot'], ['intent', 'claude'], ['intent', 'gemini'], ['intent', 'clone'],
  ['codex', 'workspace'], ['copilot', 'workspace'], ['claude', 'profile'], ['gemini', 'profile'], ['clone', 'policy'],
  ['workspace', 'agents'], ['profile', 'prompt'], ['policy', 'budget'], ['agents', 'skills'], ['setup', 'plugins'], ['prompt', 'skills'], ['budget', 'skilltests'],
  ['skills', 'githubmcp'], ['plugins', 'browser'], ['skilltests', 'apphub'], ['githubmcp', 'catalog'], ['context7', 'docs'], ['browser', 'history'],
  ['catalog', 'chunks'], ['docs', 'vector'], ['history', 'rerank'], ['chunks', 'validators'], ['vector', 'schema'], ['rerank', 'quality'],
  ['validators', 'router'], ['schema', 'routepolicy'], ['quality', 'fallback'], ['privacy', 'routepolicy'],
  ['router', 'tiny'], ['router', 'small'], ['routepolicy', 'mid'], ['fallback', 'large'], ['router', 'hostfast'], ['routepolicy', 'hostbalanced'], ['fallback', 'hostdeep'],
  ['tiny', 'localfirst'], ['small', 'splitwork'], ['mid', 'verifyroute'], ['large', 'budgetroute'], ['hostfast', 'splitwork'], ['hostbalanced', 'verifyroute'], ['hostdeep', 'budgetroute'],
  ['localfirst', 'telemetry'], ['splitwork', 'costmeter'], ['verifyroute', 'trace'], ['budgetroute', 'costmeter'],
  ['telemetry', 'guardian'], ['costmeter', 'security'], ['guardian', 'release'], ['security', 'release']
];

const state = {
  canvas: 'atlas',
  platform: localStorage.getItem('atlas-platform') || 'windows',
  zoom: 1,
  selectedNode: null,
  selectedRoute: ROUTE_DEFINITIONS[0],
  routeFilter: 'All',
  search: '',
  drag: null,
  profiles: null
};

function el(tag, className, textValue) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (textValue !== undefined) node.textContent = textValue;
  return node;
}

function svgEl(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, String(attrs[key])); });
  return node;
}

function getComponent(id) {
  return COMPONENT_DEFINITIONS.find(function (item) { return item.id === id; });
}

function laneIndex(id) {
  return LANE_DEFINITIONS.findIndex(function (lane) { return lane.id === id; });
}

function nodePosition(component) {
  return { x: component.x, y: 43 + laneIndex(component.lane) * 64 };
}

function canvasFor(id) {
  return CANVAS_DEFINITIONS.find(function (item) { return item.id === id; }) || CANVAS_DEFINITIONS[0];
}

function renderCanvasDeck() {
  const deck = document.getElementById('canvasDeck');
  deck.replaceChildren();
  CANVAS_DEFINITIONS.forEach(function (canvas, index) {
    const button = el('button', 'canvas-card' + (canvas.id === state.canvas ? ' active' : ''));
    button.type = 'button';
    button.setAttribute('role', 'listitem');
    button.setAttribute('aria-pressed', String(canvas.id === state.canvas));
    button.dataset.canvas = canvas.id;
    const header = el('header');
    header.append(el('span', '', canvas.code), el('strong', '', canvas.name));
    const mini = el('div', 'mini-map');
    LANE_DEFINITIONS.forEach(function (lane, laneNumber) {
      const mark = el('i');
      mark.style.setProperty('--x', (9 + ((laneNumber * 19 + index * 11) % 68)) + '%');
      mark.style.setProperty('--y', (5 + laneNumber * 5.55) + '%');
      mark.style.setProperty('--w', (canvas.lanes.includes(lane.id) ? 22 : 7) + '%');
      mark.style.setProperty('--tone', canvas.lanes.includes(lane.id) ? canvas.tone : 'rgba(140,148,160,.28)');
      mini.append(mark);
    });
    button.append(header, mini, el('footer', '', canvas.summary));
    button.addEventListener('click', function () { selectCanvas(canvas.id); });
    deck.append(button);
  });
}

function edgeKey(from, to) {
  return from + '>' + to;
}

function routeEdgeSet() {
  const set = new Set();
  if (!state.selectedRoute || state.canvas !== 'hybrid') return set;
  for (let i = 0; i < state.selectedRoute.nodes.length - 1; i += 1) set.add(edgeKey(state.selectedRoute.nodes[i], state.selectedRoute.nodes[i + 1]));
  return set;
}

function drawEdge(layer, fromId, toId, routeSet, focusLanes) {
  const from = getComponent(fromId);
  const to = getComponent(toId);
  if (!from || !to) return;
  const a = nodePosition(from);
  const b = nodePosition(to);
  const x1 = a.x + 146;
  const y1 = a.y + 18;
  const x2 = b.x;
  const y2 = b.y + 18;
  const bend = Math.max(70, Math.abs(x2 - x1) * .42);
  const path = svgEl('path', { d: 'M ' + x1 + ' ' + y1 + ' C ' + (x1 + bend) + ' ' + y1 + ', ' + (x2 - bend) + ' ' + y2 + ', ' + x2 + ' ' + y2, class: 'map-edge' });
  const key = edgeKey(fromId, toId);
  const reverseKey = edgeKey(toId, fromId);
  if (routeSet.has(key) || routeSet.has(reverseKey)) {
    path.classList.add('route-edge');
    path.style.setProperty('--route-color', state.selectedRoute.color);
  } else if (!focusLanes.has(from.lane) && !focusLanes.has(to.lane)) {
    path.classList.add('dim');
  }
  layer.append(path);
}

function renderMap() {
  const diagram = document.getElementById('diagram');
  const title = diagram.querySelector('title');
  const desc = diagram.querySelector('desc');
  diagram.replaceChildren(title, desc);
  const canvas = canvasFor(state.canvas);
  const focusLanes = new Set(canvas.lanes);
  const routeSet = routeEdgeSet();
  const laneLayer = svgEl('g', { class: 'lane-layer' });
  LANE_DEFINITIONS.forEach(function (lane, index) {
    const y = 16 + index * 64;
    laneLayer.append(svgEl('rect', { x: 18, y: y, width: 1884, height: 56, rx: 8, class: 'lane-band' + (index % 2 ? ' alt' : '') }));
    const idx = svgEl('text', { x: 36, y: y + 21, class: 'lane-index' });
    idx.textContent = String(index + 1).padStart(2, '0');
    const label = svgEl('text', { x: 36, y: y + 42, class: 'lane-label' });
    label.textContent = lane.name;
    laneLayer.append(idx, label);
  });
  diagram.append(laneLayer);

  const edgeLayer = svgEl('g', { class: 'edge-layer' });
  const allEdges = new Map();
  BACKBONE_EDGES.forEach(function (pair) { allEdges.set(edgeKey(pair[0], pair[1]), pair); });
  if (state.selectedRoute) {
    for (let i = 0; i < state.selectedRoute.nodes.length - 1; i += 1) {
      const pair = [state.selectedRoute.nodes[i], state.selectedRoute.nodes[i + 1]];
      allEdges.set(edgeKey(pair[0], pair[1]), pair);
    }
  }
  allEdges.forEach(function (pair) { drawEdge(edgeLayer, pair[0], pair[1], routeSet, focusLanes); });
  diagram.append(edgeLayer);

  const nodeLayer = svgEl('g', { class: 'node-layer' });
  COMPONENT_DEFINITIONS.forEach(function (component) {
    const pos = nodePosition(component);
    const group = svgEl('g', {
      class: 'map-node',
      transform: 'translate(' + pos.x + ' ' + pos.y + ')',
      tabindex: '0',
      role: 'button',
      'aria-label': component.name + '. ' + component.detail,
      'data-node': component.id
    });
    group.style.setProperty('--node-color', KIND_COLORS[component.kind]);
    group.append(svgEl('rect', { width: 146, height: 38 }));
    group.append(svgEl('circle', { cx: 13, cy: 13, r: 3, class: 'node-light' }));
    const name = svgEl('text', { x: 23, y: 16, class: 'node-title' });
    name.textContent = component.name;
    const meta = svgEl('text', { x: 13, y: 30, class: 'node-meta' });
    meta.textContent = component.lane.toUpperCase();
    group.append(name, meta);
    if (!focusLanes.has(component.lane)) group.classList.add('dim');
    if (state.selectedNode === component.id) group.classList.add('selected');
    if (state.search && (component.name + ' ' + component.detail + ' ' + component.lane).toLowerCase().includes(state.search)) group.classList.add('search-hit');
    if (state.canvas === 'hybrid' && state.selectedRoute.nodes.includes(component.id)) {
      group.classList.add('route-node');
      group.style.setProperty('--route-color', state.selectedRoute.color);
      group.classList.remove('dim');
    }
    group.addEventListener('click', function () { selectNode(component.id); });
    group.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectNode(component.id);
      }
    });
    nodeLayer.append(group);
  });
  diagram.append(nodeLayer);
  diagram.style.width = (1920 * state.zoom) + 'px';
  diagram.style.height = (1080 * state.zoom) + 'px';
  document.getElementById('zoomValue').value = Math.round(state.zoom * 100) + '%';
}

function selectCanvas(id) {
  state.canvas = id;
  const canvas = canvasFor(id);
  document.getElementById('activeCanvasName').textContent = canvas.name;
  document.getElementById('activeCanvasMeta').textContent = canvas.lanes.length + ' focused lanes · 52 components visible';
  renderCanvasDeck();
  renderMap();
}

function connectionCount(id) {
  const keys = new Set();
  BACKBONE_EDGES.forEach(function (pair) { if (pair.includes(id)) keys.add(edgeKey(pair[0], pair[1])); });
  ROUTE_DEFINITIONS.forEach(function (item) {
    item.nodes.forEach(function (nodeId, index) {
      if (nodeId === id && index < item.nodes.length - 1) keys.add(edgeKey(nodeId, item.nodes[index + 1]));
      if (nodeId === id && index > 0) keys.add(edgeKey(item.nodes[index - 1], nodeId));
    });
  });
  return keys.size;
}

function selectNode(id) {
  const component = getComponent(id);
  if (!component) return;
  state.selectedNode = id;
  document.getElementById('setupRail').dataset.component = id;
  document.querySelector('.atlas-frame').classList.add('rail-open');
  document.getElementById('railKind').textContent = component.kind + ' component';
  document.getElementById('railTitle').textContent = component.name;
  document.getElementById('railDescription').textContent = component.detail;
  const stats = document.getElementById('railStats');
  stats.replaceChildren();
  [['Lane', String(laneIndex(component.lane) + 1).padStart(2, '0')], ['Connections', connectionCount(id)]].forEach(function (pair) {
    const card = el('div', 'rail-stat');
    card.append(el('strong', '', pair[1]), el('span', '', pair[0]));
    stats.append(card);
  });
  const command = component.cmd && component.cmd[state.platform];
  const block = document.getElementById('commandBlock');
  block.hidden = !command;
  document.getElementById('railCommand').textContent = command || '';
  renderMap();
}

function renderRouteFilters() {
  const filters = ['All', 'Cost', 'Privacy', 'Quality', 'Latency', 'Offline', 'Resilience'];
  const bar = document.getElementById('routeFilters');
  bar.replaceChildren();
  filters.forEach(function (filter) {
    const button = el('button', filter === state.routeFilter ? 'active' : '', filter);
    button.type = 'button';
    button.setAttribute('aria-pressed', String(filter === state.routeFilter));
    button.addEventListener('click', function () {
      state.routeFilter = filter;
      renderRouteFilters();
      renderRouteCards();
    });
    bar.append(button);
  });
}

function renderRouteCards() {
  const grid = document.getElementById('hybridCards');
  grid.replaceChildren();
  const routes = state.routeFilter === 'All' ? ROUTE_DEFINITIONS : ROUTE_DEFINITIONS.filter(function (item) { return item.category === state.routeFilter; });
  routes.forEach(function (item) {
    const index = ROUTE_DEFINITIONS.indexOf(item) + 1;
    const button = el('button', 'route-card' + (item.id === state.selectedRoute.id ? ' active' : ''));
    button.type = 'button';
    button.style.setProperty('--route-color', item.color);
    const header = el('header');
    header.append(el('span', '', item.category), el('strong', '', String(index).padStart(2, '0')));
    const pathNames = item.nodes.slice(0, 3).map(function (id) { return getComponent(id).name; }).join(' → ');
    const footer = el('footer');
    footer.append(el('i'), el('span', '', pathNames));
    button.append(header, el('h3', '', item.name), el('p', '', item.rule), footer);
    button.addEventListener('click', function () { selectRoute(item); });
    grid.append(button);
  });
}

function selectRoute(item) {
  state.selectedRoute = item;
  renderRouteCards();
  document.getElementById('routeNumber').textContent = String(ROUTE_DEFINITIONS.indexOf(item) + 1).padStart(2, '0');
  document.getElementById('routeTitle').textContent = item.name;
  document.getElementById('routeRule').textContent = item.rule;
  document.getElementById('routeDetail').style.setProperty('--route-color', item.color);
  const path = document.getElementById('routePath');
  path.replaceChildren();
  item.nodes.forEach(function (id, index) {
    if (index) path.append(el('i', '', '→'));
    path.append(el('span', '', getComponent(id).name));
  });
  const metrics = document.getElementById('routeMetrics');
  metrics.replaceChildren();
  [['Latency', item.latency], ['Cost', item.cost], ['Privacy', item.privacy]].forEach(function (pair) {
    const wrap = el('div');
    wrap.append(el('dt', '', pair[0]), el('dd', '', pair[1]));
    metrics.append(wrap);
  });
  if (state.canvas === 'hybrid') renderMap();
}

function setZoom(next) {
  state.zoom = Math.min(1.5, Math.max(.6, next));
  renderMap();
}

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(function () { toast.classList.remove('show'); }, 1800);
}

async function loadHardware() {
  try {
    const response = await fetch('docs/hardware-profiles.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('profile unavailable');
    state.profiles = await response.json();
    renderHardware();
  } catch (error) {
    document.getElementById('hardwareSummary').textContent = 'The advisor data is unavailable in this preview. The atlas map and routes remain fully interactive.';
  }
}

function renderHardware() {
  if (!state.profiles || !state.profiles.tiers) return;
  const ram = Number(document.getElementById('ramRange').value);
  document.getElementById('ramValue').value = ram + ' GB';
  const eligible = state.profiles.tiers.filter(function (tier) { return Number(tier.ram_gb) <= ram; });
  const tier = eligible[eligible.length - 1] || state.profiles.tiers[0];
  document.getElementById('hardwareStatus').textContent = tier.verdict;
  document.getElementById('hardwareFits').textContent = tier.fits_total;
  document.getElementById('hardwareSummary').textContent = tier.summary;
  const bars = document.getElementById('hardwareBars');
  bars.replaceChildren();
  const values = Object.entries(tier.fits_by_vendor || {});
  const maximum = Math.max.apply(null, values.map(function (pair) { return pair[1]; }).concat([1]));
  values.forEach(function (pair, index) {
    const row = el('div', 'result-bar');
    const bar = el('i');
    bar.style.setProperty('--bar', Math.round(pair[1] / maximum * 100) + '%');
    bar.style.setProperty('--tone', [KIND_COLORS.compute, KIND_COLORS.capability, KIND_COLORS.instruction][index % 3]);
    row.append(el('span', '', pair[0]), bar, el('strong', '', pair[1]));
    bars.append(row);
  });
}

async function loadHealth() {
  try {
    const response = await fetch('docs/catalog-status.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('health unavailable');
    const data = await response.json();
    const counts = data.counts || {};
    document.getElementById('healthyCount').textContent = counts.HEALTHY || 0;
    document.getElementById('staleCount').textContent = counts.STALE || 0;
    document.getElementById('reviewCount').textContent = counts.REVIEW || 0;
    document.getElementById('removeCount').textContent = counts.REMOVE || 0;
    document.getElementById('healthUpdated').textContent = data.updated ? 'Snapshot ' + data.updated : 'Catalog snapshot ready';
    const privateRows = document.getElementById('healthRows');
    if (privateRows && Array.isArray(data.repos)) {
      privateRows.replaceChildren();
      data.repos.slice(0, 12).forEach(function (row) { privateRows.append(el('p', '', String(row.repo || 'Private record') + ' · ' + String(row.status || 'UNKNOWN'))); });
    }
  } catch (error) {
    document.getElementById('healthUpdated').textContent = 'Catalog signal unavailable';
  }
}

async function checkBuild() {
  const localId = document.querySelector('meta[name="build-id"]').content;
  document.getElementById('buildLabel').textContent = localId;
  if (localId === 'dev') return;
  try {
    const response = await fetch('version.json?check=' + Date.now(), { cache: 'no-store' });
    const current = await response.json();
    if (current.build_id && current.build_id !== localId) document.getElementById('staleBar').hidden = false;
  } catch (error) {
    return;
  }
}

function bindControls() {
  document.getElementById('themeToggle').addEventListener('click', function () {
    const html = document.documentElement;
    const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
    html.dataset.theme = next;
    localStorage.setItem('atlas-theme', next);
  });
  const savedTheme = localStorage.getItem('atlas-theme');
  if (savedTheme === 'light' || savedTheme === 'dark') document.documentElement.dataset.theme = savedTheme;

  document.querySelectorAll('#platSeg button').forEach(function (button) {
    const active = button.dataset.platform === state.platform;
    button.setAttribute('aria-pressed', String(active));
    button.addEventListener('click', function () {
      state.platform = button.dataset.platform;
      localStorage.setItem('atlas-platform', state.platform);
      document.querySelectorAll('#platSeg button').forEach(function (item) { item.setAttribute('aria-pressed', String(item === button)); });
      if (state.selectedNode) selectNode(state.selectedNode);
      renderHardware();
    });
  });
  document.getElementById('mapSearch').addEventListener('input', function (event) {
    state.search = event.target.value.trim().toLowerCase();
    renderMap();
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) {
      event.preventDefault();
      document.getElementById('mapSearch').focus();
    }
    if (event.key === 'Escape') {
      document.querySelector('.atlas-frame').classList.remove('rail-open');
      state.selectedNode = null;
      renderMap();
    }
  });
  document.getElementById('zoomIn').addEventListener('click', function () { setZoom(state.zoom + .1); });
  document.getElementById('zoomOut').addEventListener('click', function () { setZoom(state.zoom - .1); });
  document.getElementById('zoomReset').addEventListener('click', function () { setZoom(1); });
  document.getElementById('railClose').addEventListener('click', function () { document.querySelector('.atlas-frame').classList.remove('rail-open'); state.selectedNode = null; renderMap(); });
  document.getElementById('copyCommand').addEventListener('click', async function () {
    const command = document.getElementById('railCommand').textContent;
    try { await navigator.clipboard.writeText(command); showToast('Command copied'); } catch (error) { showToast('Select and copy the command manually'); }
  });
  document.getElementById('traceRoute').addEventListener('click', function () {
    selectCanvas('hybrid');
    document.getElementById('atlas').scrollIntoView({ behavior: 'smooth', block: 'start' });
    showToast('Tracing ' + state.selectedRoute.name);
  });
  document.getElementById('hardwareRoute').addEventListener('click', function () {
    const ram = Number(document.getElementById('ramRange').value);
    const target = ram >= 24 ? ROUTE_DEFINITIONS.find(function (item) { return item.id === 'offline-04'; }) : ram >= 12 ? ROUTE_DEFINITIONS.find(function (item) { return item.id === 'cost-02'; }) : ROUTE_DEFINITIONS.find(function (item) { return item.id === 'latency-02'; });
    state.routeFilter = 'All';
    selectRoute(target);
    document.getElementById('routes').scrollIntoView({ behavior: 'smooth' });
  });
  document.getElementById('ramRange').addEventListener('input', renderHardware);
  document.getElementById('staleReload').addEventListener('click', function () {
    const target = new URL(window.location.href);
    target.searchParams.set('fresh', Date.now());
    window.location.replace(target.toString());
  });

  const viewport = document.getElementById('mapViewport');
  viewport.addEventListener('pointerdown', function (event) {
    if (event.target.closest('.map-node')) return;
    state.drag = { x: event.clientX, y: event.clientY, left: viewport.scrollLeft, top: viewport.scrollTop };
    viewport.classList.add('dragging');
    viewport.setPointerCapture(event.pointerId);
  });
  viewport.addEventListener('pointermove', function (event) {
    if (!state.drag) return;
    viewport.scrollLeft = state.drag.left - (event.clientX - state.drag.x);
    viewport.scrollTop = state.drag.top - (event.clientY - state.drag.y);
  });
  viewport.addEventListener('pointerup', function () { state.drag = null; viewport.classList.remove('dragging'); });
  viewport.addEventListener('pointercancel', function () { state.drag = null; viewport.classList.remove('dragging'); });
}

function assertRegistry() {
  const errors = [];
  if (LANE_DEFINITIONS.length < 15 || LANE_DEFINITIONS.length > 20) errors.push('lane count must remain between 15 and 20');
  if (CANVAS_DEFINITIONS.length < 10) errors.push('canvas count must remain at least 10');
  if (ROUTE_DEFINITIONS.length <= 30) errors.push('route count must remain above 30');
  if (COMPONENT_DEFINITIONS.length !== ATLAS_META.componentCount) errors.push('component registry does not match metadata');
  if (LANE_DEFINITIONS.length !== ATLAS_META.laneCount || CANVAS_DEFINITIONS.length !== ATLAS_META.canvasCount || ROUTE_DEFINITIONS.length !== ATLAS_META.routeCount) errors.push('atlas registry does not match metadata');
  if (errors.length) throw new Error(errors.join('; '));
}

function init() {
  assertRegistry();
  bindControls();
  renderCanvasDeck();
  renderMap();
  renderRouteFilters();
  selectRoute(state.selectedRoute);
  loadHardware();
  loadHealth();
  checkBuild();
}

document.addEventListener('DOMContentLoaded', init);
