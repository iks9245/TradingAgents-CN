import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../', import.meta.url))
const baseline = JSON.parse(readFileSync(new URL('./typecheck-baseline.json', import.meta.url), 'utf8'))
const result = spawnSync(process.execPath, ['node_modules/vue-tsc/bin/vue-tsc.js', '--noEmit', '--pretty', 'false'], {
  cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
})
if (result.error || result.signal) {
  console.error(result.error || result.signal)
  process.exit(1)
}
const output = `${result.stdout || ''}${result.stderr || ''}`
const diagnostics = {}
for (const line of output.split(/\r?\n/)) {
  const match = line.match(/^(.*?)\(\d+,\d+\): error (TS\d+): (.*)$/)
  if (match) {
    const key = `${match[1]}: ${match[2]}: ${match[3]}`
    diagnostics[key] = (diagnostics[key] || 0) + 1
  } else if (/error TS\d+:/.test(line)) {
    // Configuration/global errors must never disappear into the baseline.
    console.error(line)
    process.exit(1)
  }
}
if (result.status !== 0 && Object.keys(diagnostics).length === 0) {
  console.error(output)
  process.exit(1)
}
let regressions = 0
for (const [key, count] of Object.entries(diagnostics)) {
  const added = count - (baseline.diagnostics[key] || 0)
  if (added > 0) {
    console.error(`NEW (${added}): ${key}`)
    regressions += added
  }
}
const total = Object.values(diagnostics).reduce((a, b) => a + b, 0)
console.log(`Type check: ${total} existing diagnostics; ${regressions} new diagnostics.`)
console.log('This regression gate does not mean the full strict type check passes.')
process.exit(regressions ? 1 : 0)
