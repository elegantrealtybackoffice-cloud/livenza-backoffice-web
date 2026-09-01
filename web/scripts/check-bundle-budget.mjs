import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const manifestPath = path.join(root, '.next', 'build-manifest.json')
const sharedBudget = 250 * 1024
const chunkBudget = 180 * 1024
const compressedEquivalentRatio = 0.35

if (!fs.existsSync(manifestPath)) {
  console.error('Missing .next/build-manifest.json. Run npm run build first.')
  process.exit(2)
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
const listed = new Set([
  ...(manifest.polyfillFiles ?? []),
  ...(manifest.rootMainFiles ?? []),
  ...Object.values(manifest.pages ?? {}).flat(),
].filter(file => typeof file === 'string' && file.endsWith('.js')))

let sharedRaw = 0
for (const file of listed) {
  const full = path.join(root, '.next', file)
  if (fs.existsSync(full)) sharedRaw += fs.statSync(full).size
}
const compressedEquivalent = Math.round(sharedRaw * compressedEquivalentRatio)
if (compressedEquivalent > sharedBudget) {
  console.error(`Shared initial JS estimate ${compressedEquivalent} exceeds ${sharedBudget} bytes.`)
  process.exit(1)
}

const chunksDir = path.join(root, '.next', 'static', 'chunks')
if (fs.existsSync(chunksDir)) {
  for (const file of fs.readdirSync(chunksDir)) {
    const full = path.join(chunksDir, file)
    if (!file.endsWith('.js') || !fs.statSync(full).isFile()) continue
    const size = fs.statSync(full).size
    if (size > chunkBudget) {
      console.error(`Client chunk ${file} is ${size} bytes and exceeds ${chunkBudget} bytes; allowlist is empty at launch.`)
      process.exit(1)
    }
  }
}
console.log(`Bundle budget OK: shared estimate ${compressedEquivalent} bytes.`)
