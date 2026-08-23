import assert from 'node:assert/strict'
import { dashboardFromHash, dashboardHash, hashSlug } from '../src/app/dashboardRoute.js'

const dashboards = [
  { id: 'tab-story', slug: 'historia', aliases: ['storytelling'] },
  { id: 'tab-power', slug: 'poder-adquisitivo' },
  { id: 'tab-poverty', slug: 'pobreza' },
  { id: 'tab-pendulo', slug: 'pendulo-poder-economico', aliases: ['pendulo-distributivo'] },
  { id: 'tab-roads', slug: 'rutas-publico-privado' },
  { id: 'tab-tourism', slug: 'vacaciones-turismo' },
]

assert.equal(dashboardFromHash('', dashboards).id, 'tab-story')
assert.equal(dashboardFromHash('#/', dashboards).id, 'tab-story')
assert.equal(dashboardFromHash('#/historia', dashboards).id, 'tab-story')
assert.equal(dashboardFromHash('#/storytelling', dashboards).id, 'tab-story')
assert.equal(dashboardFromHash('#/pobreza', dashboards).id, 'tab-poverty')
assert.equal(dashboardFromHash('#/tab-poverty', dashboards).id, 'tab-poverty')
assert.equal(dashboardFromHash('#/pendulo-poder-economico', dashboards).id, 'tab-pendulo')
assert.equal(dashboardFromHash('#/pendulo-distributivo', dashboards).id, 'tab-pendulo')
assert.equal(dashboardFromHash('#/rutas-publico-privado', dashboards).id, 'tab-roads')
assert.equal(dashboardFromHash('#/vacaciones-turismo', dashboards).id, 'tab-tourism')
assert.equal(dashboardFromHash('#/no-existe', dashboards).id, 'tab-story')
assert.equal(hashSlug('#/pobreza/'), 'pobreza')
assert.equal(dashboardHash(dashboards[2]), '#/pobreza')

console.log('Ruta raíz y enlaces directos de dashboards verificados.')
