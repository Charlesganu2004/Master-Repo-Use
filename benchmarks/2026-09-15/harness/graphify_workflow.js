export const meta = {
  name: 'graphify-harness-experiment',
  description: 'Four arms (no harness, no harness plus graphify, base harness, super harness) on two codebase questions, three reps, every answer capped at 400 tokens',
  phases: [{ title: 'Ask', detail: 'Explore scaffold, Sonnet 5, graphify available locally' }],
}

const ARMS = ['bare_nograph', 'bare_strict', 'bare_graph', 'base_graph', 'super_graph']
const TASKS = ['g1', 'g2']

const items = []
for (let rep = 1; rep <= ARGS.reps; rep++)
  for (const task of TASKS)
    for (const arm of ARMS)
      items.push({ task, arm, rep })
log(`${items.length} runs, 400-token ceiling on every one`)

phase('Ask')
const results = await pipeline(
  items,
  item => agent(ARGS.prompts[item.task][item.arm], {
    label: `ask|${item.task}|${item.arm}|r${item.rep}`, phase: 'Ask',
    agentType: 'Explore', model: 'sonnet',
  }).then(text => ({ ...item, answered: Boolean(text) })),
)

const done = results.filter(Boolean)
log(`${done.filter(r => r.answered).length}/${items.length} answered`)
return done.map(r => `${r.task}|${r.arm}|r${r.rep}:${r.answered ? 'ok' : 'empty'}`)
