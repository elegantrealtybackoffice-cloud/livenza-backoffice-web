import fs from 'node:fs'
import path from 'node:path'
const routes = ['stays','store','fit','groom','skin','media','life','about','contact','account','stays/book']
const missing = routes.filter(route => !fs.existsSync(path.join(process.cwd(), 'src', 'app', route, 'page.tsx')))
if (missing.length) { console.error(`Missing route pages: ${missing.join(', ')}`); process.exit(1) }
console.log(`Route source audit OK: ${routes.length + 1} top-level/handoff routes.`)
