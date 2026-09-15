export const meta = {
  name: 'browser-tool-benchmark',
  description: 'caveman-browse vs Playwright vs Rustwright: an agent does three browser tasks with each tool, three reps, one run per tool at a time',
  phases: [{ title: 'Browse', detail: 'Explore scaffold, Sonnet 5; batches of one run per tool' }],
}

const TOOLS = ['caveman-browse', 'playwright', 'rustwright']
const TASKS = ['lookup', 'count', 'checkout']

function fill(text, values) {
  return Object.entries(values).reduce((out, [key, value]) => out.split(`{${key}}`).join(value), text)
}

function prompt(tool, task, rep) {
  const home = `${args.homesRoot}\\${task}-r${rep}`
  const port = String(9700 + (rep - 1) * TASKS.length + TASKS.indexOf(task))
  const card = fill(args.tools[tool], {
    PY: args.py, EDGE: args.edge, CB: args.cb, HOME: home, PORT: port,
    CAVEMAN_BROWSE_GUIDE: args.guide,
  })
  return `${card}\n\nTask: ${fill(args.tasks[task], { BASE: args.base })}\n\n${args.footer}`
}

phase('Browse')
const results = []
for (let rep = 1; rep <= args.reps; rep++) {
  for (const task of TASKS) {
    // One run per tool at a time: a tool never shares its browser or port with
    // itself, and the three tools see the same moment of machine load.
    const batch = await parallel(TOOLS.map(tool => () =>
      agent(prompt(tool, task, rep), {
        label: `browse|${task}|${tool}|r${rep}`, phase: 'Browse', agentType: 'Explore', model: 'sonnet',
      }).then(text => ({ tool, task, rep, text }))))
    results.push(...batch.filter(Boolean))
    log(`rep ${rep} ${task}: ${batch.filter(Boolean).length}/3 returned`)
  }
}
return results.map(r => {
  const line = (r.text || '').split('\n').reverse().find(l => /ANSWER:/.test(l)) || ''
  return { label: `${r.task}|${r.tool}|r${r.rep}`, answer: line.replace(/^.*ANSWER:\s*/, '').trim() }
})
