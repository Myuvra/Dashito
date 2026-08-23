import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'

const sourcePath = resolve('data/legacy-archive/legacy.html')
const outputPath = resolve('public/papitas-pattern.svg')
const html = await readFile(sourcePath, 'utf8')
const matches = [...html.matchAll(/data:image\/svg\+xml;base64,([A-Za-z0-9+/=]+)/g)]

if (!matches.length) throw new Error('No se encontró el patrón SVG de papitas en la maqueta archivada.')

const encoded = matches
  .map((match) => match[1])
  .sort((left, right) => right.length - left.length)[0]

const svg = Buffer.from(encoded, 'base64').toString('utf8')

if (!svg.includes('<svg') || !svg.includes('</svg>')) throw new Error('El recurso recuperado no es un SVG válido.')

await mkdir(dirname(outputPath), { recursive: true })
await writeFile(outputPath, svg, 'utf8')
console.log(`Patrón original recuperado en ${outputPath}`)
