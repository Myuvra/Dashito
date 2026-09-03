# Épica de transición · railway-dashboard como source único

**Fecha:** 2026-09-03 · **Estado:** porting en verde, sin commit/deploy (lo decide el usuario).

Documento vivo que reemplaza al viejo `GAPS_FRENTE_A.md`. Describe el cambio de
source y qué quedó portado, para que no haya confusión sobre qué manda.

---

## 1. Qué cambió (el "port viejo" → el nuevo)

- **Source de verdad = `Tuneando inflacion/railway-dashboard/index.html`** (el bundle
  deployable Railway/Netlify). Antes el pipeline leía `Legacy/inflacion/index.html`.
- `Legacy/inflacion/` **ya no es el source**; sólo sobrevive como **`dataRoot`
  fallback**: el bundle es mínimo y no trae `data/derivados/` ni los dossiers
  pesados, así que el importador cae ahí para esas descargas mientras exista.
- El importador (`scripts/import-legacy-parity.mjs`) es **data-driven**: deriva
  tabs y scripts del propio source; no hay conteos fijos.

## 2. Tabs nuevos portados en esta transición

| Tab | id | Origen | Render | Estado |
|---|---|---|---|---|
| Patrimonio político · DDJJ | `tab-political-wealth` | `assets/political-wealth-tab.js` + `political-wealth-data.js` (4,7 MB, bootstrap) · datos `research/political_wealth_2026-09-01/` | `renderPoliticalWealth` | ✅ 3 charts + roster + tematizado |
| Hogares en mora · propuesta | `tab-mora-ley` | `assets/mora-ley-tab.js` (dossier `Mora/`) | `renderMoraLey` | ✅ migrado al bundle |
| Costo del crédito · reclamo | `tab-reclamo-credito` | `assets/reclamo-credito-tab.js` (dossier `Reclamo colectivo/`) | `renderReclamoCredito` | ✅ migrado al bundle |

Mora y Reclamo (Frente B) **se conservan** y se **migraron al bundle**
railway-dashboard (assets + `<script>` en su index.html) para que el deploy del
legacy también los tenga.

## 3. Cómo funciona el porting de assets (pre-materialización)

Los tabs vienen como IIFEs que inyectan style + nav + secciones en runtime. Como
el `LegacyMarkup` de Dashito reconstruye el markup como elementos React (no
innerHTML) y descarta `<script>`, el importador **pre-materializa**:
`parseEpicaAsset()` extrae el `<style>` (→ base.css), los botones (→ controls),
las secciones top-level (→ tabs.html) y deja sólo el JS de render (→
`runtime-epica-NN.js`). Clasifica cada `insertAdjacentHTML` por **contenido**
(`<section>`→panel, `tab-btn`→nav, resto se deja — p.ej. un `<th>` dentro de un
render), y soporta cualquier comilla (backtick / ' / ") y `?v=` en los `src`.

Los data-only (`political-wealth-data.js`) pasan enteros como runtime y cargan
**antes** que su tab (orden del source preservado).

## 4. Cableado que se toca al sumar un tab

1. `scripts/import-legacy-parity.mjs` — auto (data-driven). Copia `research/*` y
   derivados desde `dataRoot`.
2. `src/app/dashboardRegistry.js` — **metadata obligatoria** por id (sin ella
   crashea `dashboards`) + categoría.
3. `src/features/legacy-parity/LegacyParityFeature.jsx` — `legacyTabRenderers`.
4. themeSource `data/legacy-archive/dashito-legacy.css` — tokens `--da-*` para las
   clases nuevas, los 3 skins.
5. Cache-bust en `src/styles.css` + `legacyRuntimeVersion` (actual **migracion9**).

## 5. Estado / verificación

- **46 tabs** (37 estáticos + 6 EPICA + political-wealth + mora + reclamo).
- Tests: `parity` **235/235**, `theme-audit` **753/753** (0 en cola), `routing`,
  `responsive`, `epic` verdes.
- En vivo: political-wealth (data + 3 charts + roster), mora (3), reclamo (3)
  renderizan y tematizan (`--da-surface` en dark). Fix de doble-render (90+420 ms)
  para deep-links en frío.
- Resolución de datos: los sources-box de Mora/Reclamo linkean la **fuente real
  BCRA** primero (URLs verificadas) con copia archivada `/data/…` como fallback.

## 6. Docs viejos retirados / a revisar

- **Retirado:** `Dashito/GAPS_FRENTE_A.md` (auditoría del port viejo contra
  `Legacy/inflacion`, ya superada por este documento).
- **Candidatos a limpiar** (registros del usuario, no los borro sin confirmar):
  `Legacy/inflacion/BACKUP_ACTUALIZACION_2026-08-*.md` / `-09-01.md` — describen
  las actualizaciones del source viejo; pueden confundir sobre qué manda hoy.

## 7. Pendiente

- Confirmar borrado de los changelogs viejos (punto 6).
- ¿Migrar también los CSV de descarga de Mora/Reclamo al bundle, o alcanza con la
  fuente BCRA + fallback en el repo completo?
- Commit/deploy sólo cuando el usuario lo pida.
