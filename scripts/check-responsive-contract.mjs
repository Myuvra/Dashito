import assert from 'node:assert/strict'
import fs from 'node:fs'

const shell = fs.readFileSync('src/styles.css', 'utf8')
const legacy = fs.readFileSync('data/legacy-archive/dashito-legacy.css', 'utf8')
const app = fs.readFileSync('src/AppNext.jsx', 'utf8')

const profiles = [
  { name: '9:16', width: 390, height: 693, mode: 'mobile' },
  { name: '2:3', width: 600, height: 900, mode: 'mobile' },
  { name: '4:5', width: 768, height: 960, mode: 'mobile' },
  { name: '1:1', width: 900, height: 900, mode: 'drawer' },
  { name: '5:4', width: 1180, height: 944, mode: 'compact' },
  { name: '3:2', width: 1280, height: 853, mode: 'compact' },
  { name: '16:9', width: 1440, height: 810, mode: 'wide' },
]

for (const breakpoint of ['1280px', '1000px', '768px', '620px', '380px', '800px', '760px', '560px']) {
  assert.ok(shell.includes(breakpoint), `falta el breakpoint de shell ${breakpoint}`)
}

for (const breakpoint of ['1180px', '900px', '768px', '620px', '520px', '380px', '800px', '560px']) {
  assert.ok(legacy.includes(breakpoint), `falta el breakpoint Legacy ${breakpoint}`)
}

assert.match(shell, /orientation:\s*landscape/)
assert.match(legacy, /orientation:\s*landscape/)
assert.match(app, /drawer:\s*1000/)
assert.match(app, /compact:\s*1280/)
assert.match(app, /matchMedia/)
assert.match(shell, /background-repeat:\s*repeat/, 'el patrón de papitas debe repetirse en el canvas')
assert.match(shell, /background-size:\s*clamp\(320px,32vw,470px\) auto/, 'el patrón de escritorio debe conservar el tamaño Legacy')
assert.match(shell, /background-size:\s*300px 300px/, 'el patrón móvil debe conservar el tamaño Legacy')
assert.doesNotMatch(legacy, /content:\s*'🥔'/, 'no debe haber papas gigantes dentro de los cuadros')

for (const profile of profiles) {
  const mode = profile.width <= 768
    ? 'mobile'
    : profile.width <= 1000
      ? 'drawer'
      : profile.width <= 1280
        ? 'compact'
        : 'wide'
  assert.equal(mode, profile.mode, `${profile.name} cayó en un modo inesperado`)
}

console.log(`Responsive Dashito: ${profiles.length} relaciones representativas cubiertas por cuatro modos de shell.`)
