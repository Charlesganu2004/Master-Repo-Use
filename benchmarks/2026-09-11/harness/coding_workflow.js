export const meta = {
  name: 'harness-skill-benchmark',
  description: 'Six prompt arms x two coding tasks x five reps on Sonnet 5 in a clean scaffold, each answer blind-judged twice by Opus 5',
  phases: [
    { title: 'Run', detail: 'Explore scaffold (no CLAUDE.md), Sonnet 5, one answer per arm, task and rep' },
    { title: 'Judge', detail: 'two blind Opus 5 judges per answer, rubric scored 1-10' },
  ],
}

// Mirrors benchmarks/2026-09-11/harness/build_arms.py exactly. Every transcript's
// first message is checked against the sha256 in arms/manifest.json afterwards,
// so a divergence here is caught, not measured.
const ARMS = ['bare', 'super', 'super_ponytail_caveman', 'super_ponytail_nocaveman', 'ponytail', 'caveman']
const NO_SKILLS = new Set(['bare', 'ponytail', 'caveman'])
const TASKS = ['t1', 't2']

function withoutCaveman(ctx) {
  const lines = ctx.split('\n')
  const drop = prefix => {
    const hits = lines.filter(l => l.startsWith(prefix)).length
    if (hits !== 1) throw new Error(`expected one line starting ${prefix}, found ${hits}`)
    lines.splice(lines.findIndex(l => l.startsWith(prefix)), 1)
  }
  drop('1. CAVEMAN.')
  const from = 'RE-APPLY LAYER 1 to what you produced: caveman, full output, anti-slop, again.'
  const at = lines.findIndex(l => l.includes(from))
  if (at < 0) throw new Error('re-apply line not found')
  lines[at] = lines[at].replace(from, 'RE-APPLY LAYER 1 to what you produced: full output, anti-slop, again.')
  drop('S1. CAVEMAN')
  const out = lines.join('\n')
  if (out.toLowerCase().includes('caveman')) throw new Error('no-caveman context still mentions caveman')
  return out
}

function context(arm, task) {
  const sup = args.superCtx[task]
  if (arm === 'bare') return ''
  if (arm === 'super') return sup
  if (arm === 'super_ponytail_caveman') return sup + '\n\n' + args.ponytail + '\n\n' + args.caveman
  if (arm === 'super_ponytail_nocaveman') return withoutCaveman(sup) + '\n\n' + args.ponytail
  if (arm === 'ponytail') return args.ponytail
  if (arm === 'caveman') return args.caveman
  throw new Error(`unknown arm ${arm}`)
}

function prompt(arm, task) {
  const parts = []
  const ctx = context(arm, task)
  if (ctx) parts.push('<system-reminder>\nUserPromptSubmit hook additional context: ' + ctx + '\n</system-reminder>')
  parts.push(args.tasks[task])
  parts.push(NO_SKILLS.has(arm) ? args.delivery + ' ' + args.noSkills : args.delivery)
  return parts.join('\n\n')
}

const SCORE = { type: 'integer', minimum: 1, maximum: 10 }
const JUDGE = {
  type: 'object',
  properties: {
    correctness: SCORE, code_quality: SCORE, test_quality: SCORE,
    instruction_following: SCORE, communication: SCORE, overall: SCORE,
    three_sentence_note: { type: ['boolean', 'null'] },
    lists_unhandled_edge_cases: { type: ['boolean', 'null'] },
    strengths: { type: 'string' }, weaknesses: { type: 'string' },
  },
  required: ['correctness', 'code_quality', 'test_quality', 'instruction_following', 'communication',
             'overall', 'three_sentence_note', 'lists_unhandled_edge_cases', 'strengths', 'weaknesses'],
}

function judgePrompt(task, answer, which) {
  return `You are judge ${which} of 2 grading one answer to a programming request. You do not know how the answer was produced and should not guess. Do not use any tools: judge only from the text below.

Score each dimension from 1 to 10. Anchors: 10 could not be meaningfully better; 7 solid with minor issues; 4 real problems a reviewer would block on; 1 wrong or missing.
- correctness: would the implementation behave correctly for everything the request specifies? Read the code and trace the cases the request settles.
- code_quality: clear and idiomatic, with no needless complexity and no missing necessary structure.
- test_quality: do the tests exercise the specified behaviour, including the error cases${task === 't2' ? ' and concurrent callers' : ''}?
- instruction_following: did it deliver every part that was asked for, in the requested format?
- communication: is the prose clear, accurate and appropriately brief for the person reading it, without filler or unsupported claims?
- overall: your holistic grade.
${task === 't2'
    ? 'Also report three_sentence_note (true only if it wrote a note of exactly three sentences on why it chose the data structure) and lists_unhandled_edge_cases (true only if it finished by listing edge cases it did not handle).'
    : 'Set three_sentence_note and lists_unhandled_edge_cases to null: they apply only to a different task.'}

REQUEST:
${args.tasks[task]}

ANSWER:
${answer}`
}

const items = []
for (let rep = 1; rep <= args.reps; rep++)
  for (const task of TASKS)
    for (const arm of ARMS)
      items.push({ task, arm, rep })
log(`${items.length} runs, ${items.length * 2} judgements`)

phase('Run')
const results = await pipeline(
  items,
  item => agent(prompt(item.arm, item.task), {
    label: `code|${item.task}|${item.arm}|r${item.rep}`, phase: 'Run', agentType: 'Explore', model: 'sonnet',
  }),
  (answer, item) => {
    // Judges score the first three runs of every cell. Every run is still
    // scored by the hidden tests; the judges add the reading a test cannot do,
    // and three per cell is enough for that at a third of the judging cost.
    // One Opus judge and one Sonnet judge: the answers are Sonnet's, so a
    // panel of only Sonnet judges could be marking its own homework.
    if (!answer || Number(item.rep) > 3) return { ...item, answered: Boolean(answer), judges: [] }
    const models = { 1: 'opus', 2: 'sonnet' }
    return parallel([1, 2].map(which => () => agent(judgePrompt(item.task, answer, which), {
      label: `judge|${item.task}|${item.arm}|r${item.rep}|j${which}`, phase: 'Judge',
      agentType: 'Explore', model: models[which], schema: JUDGE,
    }))).then(judges => ({ ...item, answered: true, judges }))
  },
)

const done = results.filter(Boolean)
log(`${done.filter(r => r.answered).length}/${items.length} answered, ${done.flatMap(r => r.judges).filter(Boolean).length} judgements`)
return done.map(r => ({
  label: `${r.task}|${r.arm}|r${r.rep}`,
  overall: r.judges.filter(Boolean).map(j => j.overall),
}))
