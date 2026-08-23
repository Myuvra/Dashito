from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_146_pendulo_cft_rentabilidad.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_147_pendulo_botoneras_horizontales.html"
INDEX_HTML = ROOT / "index.html"
DERIVED_DIR = ROOT / "data" / "derivados" / "pendulo_poder_economico"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_BOTONERAS_HORIZONTALES_V147.md"
TESTS_JSON = DERIVED_DIR / "TESTS_BOTONERAS_HORIZONTALES_V147.json"


HORIZONTAL_CSS = r'''
<style id="pendulo-poder-horizontal-controls-v147-style">
/* v147 · botoneras horizontales próximas al gráfico que modifican */
#tab-pendulo .pend-layer-nav-wrap{position:sticky;top:0;z-index:18;padding:7px 0;background:linear-gradient(180deg,rgba(255,248,253,.98) 70%,rgba(255,248,253,0));backdrop-filter:blur(7px)}
#tab-pendulo .pend-layer-nav{display:flex;flex-wrap:nowrap;gap:7px;max-width:100%;overflow-x:auto;overflow-y:hidden;padding:3px 2px 8px;scrollbar-width:thin;scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch}
#tab-pendulo .pend-layer-btn{flex:0 0 auto;scroll-snap-align:center;white-space:nowrap}
#tab-pendulo .pend-controls-context{display:flex;align-items:center;gap:7px;margin:12px 0 6px;color:#7a657f;font-size:8.8px;font-weight:800;line-height:1.35}
#tab-pendulo .pend-controls-context::before{content:'↳';display:inline-grid;place-items:center;width:19px;height:19px;border-radius:999px;background:#f2e8f7;color:#714b84;font-size:12px;font-weight:950}
#tab-pendulo .pend-controls.pend-controls-near-chart{display:flex;align-items:center;gap:8px;max-width:100%;margin:0 0 9px;padding:8px;border:1px solid #ddcfe6;border-radius:16px;background:linear-gradient(90deg,#fbf7ff,#fff);overflow-x:auto;overflow-y:hidden;scrollbar-width:thin;scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch;box-sizing:border-box}
#tab-pendulo .pend-controls-near-chart .pend-control{display:flex;align-items:center;gap:8px;flex:0 0 auto;padding:5px 8px;border:0;border-right:1px solid #e4d9e9;border-radius:0;background:transparent;scroll-snap-align:start}
#tab-pendulo .pend-controls-near-chart .pend-control:last-child{border-right:0}
#tab-pendulo .pend-controls-near-chart .pend-control>span{flex:0 0 auto;margin:0;color:#846a8e;white-space:nowrap}
#tab-pendulo .pend-controls-near-chart .pend-buttons{display:flex;flex-wrap:nowrap;gap:6px}
#tab-pendulo .pend-controls-near-chart .pend-btn{flex:0 0 auto;padding:7px 10px;white-space:nowrap}
#tab-pendulo .pend-controls-near-chart .pend-control-toggle{cursor:pointer}
#tab-pendulo .pend-controls-near-chart .pend-toggle-action{display:flex;align-items:center;gap:6px;color:#5d3c69;font-size:9px;font-weight:950;text-transform:none;letter-spacing:0}
#tab-pendulo .pend-controls-near-chart .pend-toggle-action input{width:16px;height:16px;margin:0;accent-color:#80539a}
#tab-pendulo .pend-controls-near-chart .pend-toggle-note{color:#8b758f;font-size:7.8px;font-weight:700;letter-spacing:0;text-transform:none}
@media(max-width:760px){
 #tab-pendulo .pend-layer-nav-wrap{top:0;margin-left:-2px;margin-right:-2px}
 #tab-pendulo .pend-controls.pend-controls-near-chart{display:grid;grid-template-columns:minmax(0,1fr);gap:3px;margin-left:-2px;margin-right:-2px;overflow:visible}
 #tab-pendulo .pend-controls-near-chart .pend-control{display:flex;width:100%;min-width:0;max-width:100%;padding:5px 7px;border-right:0;border-bottom:1px solid #e4d9e9;overflow-x:auto;overflow-y:hidden;scrollbar-width:thin;box-sizing:border-box}
 #tab-pendulo .pend-controls-near-chart .pend-control:last-child{border-bottom:0}
 #tab-pendulo .pend-controls-near-chart .pend-control>span{position:sticky;left:0;z-index:2;padding:5px 7px 5px 1px;background:#fbf8fd}
 #tab-pendulo .pend-controls-near-chart .pend-control-toggle{overflow-x:hidden}
 #tab-pendulo .pend-controls-near-chart .pend-toggle-note{display:none}
 #tab-pendulo .pend-controls-near-chart .pend-btn{padding:7px 9px}
}
</style>
'''


def main() -> None:
    source = SOURCE_HTML.read_text(encoding="utf-8")
    text = source

    control_match = re.search(
        r'        <div class="pend-controls">\s*'
        r'<div class="pend-control"><span>Ver como</span>.*?'
        r'<div class="pend-control"><span>Serie</span>.*?'
        r'        </div>\s*',
        text,
        flags=re.DOTALL,
    )
    if control_match is None:
        raise RuntimeError("No se encontró la botonera original de Producción")

    controls = control_match.group(0).strip()
    controls = controls.replace(
        '<div class="pend-controls">',
        '<div class="pend-controls pend-controls-near-chart" aria-label="Controles del gráfico principal" data-controls-for="pendMainChart">',
        1,
    )
    controls = controls.replace(
        '<div class="pend-control"><span>Ver como</span>',
        '<div class="pend-control" role="group" aria-label="Ver gráfico como"><span>Ver como</span>',
        1,
    )
    controls = controls.replace(
        '<div class="pend-control"><span>Serie</span>',
        '<div class="pend-control" role="group" aria-label="Elegir universo de la serie"><span>Serie</span>',
        1,
    )
    text = text[: control_match.start()] + text[control_match.end() :]

    average_match = re.search(
        r'        <label class="pend-average-control"><input id="pendAverageToggle".*?</label>\s*',
        text,
        flags=re.DOTALL,
    )
    if average_match is None:
        raise RuntimeError("No se encontró el control de promedios")
    text = text[: average_match.start()] + text[average_match.end() :]
    average_control = (
        '<label class="pend-control pend-control-toggle" role="group" aria-label="Guías del gráfico">'
        '<span>Guías</span><span class="pend-toggle-action"><input id="pendAverageToggle" type="checkbox" checked>'
        '<b>Promedio por gobierno</b></span><span class="pend-toggle-note">Sólo dentro de cada tramo comparable</span></label>'
    )
    controls = controls.rsplit('</div>', 1)[0] + '\n          ' + average_control + '\n        </div>'

    chart_heading = (
        '        <div class="pend-head"><div><h3>El péndulo distributivo argentino</h3>'
        '<p class="pend-note">+100 = todo hacia trabajo/hogares · 0 = empate distributivo · '
        '−100 = todo hacia excedente societario. Los umbrales descriptivos ±10 no son una clasificación científica.</p></div></div>'
    )
    if chart_heading not in text:
        raise RuntimeError("No se encontró el encabezado del gráfico principal")
    chart_match = re.search(
        r'\s*<div class="pend-chart-scroll"><div id="pendMainChart" class="pend-chart"></div></div>',
        text,
    )
    if chart_match is None:
        raise RuntimeError("No se encontró el contenedor del gráfico principal")
    chart_anchor = chart_match.group(0).lstrip()
    controls_and_chart = (
        '        <div class="pend-controls-context">Todos estos controles actualizan el gráfico de abajo.</div>\n        '
        + controls
        + '\n'
        + chart_anchor
    )
    text = text[: chart_match.start()] + '\n' + controls_and_chart + text[chart_match.end() :]
    text = text.replace("</head>", HORIZONTAL_CSS + "\n</head>", 1)
    text = text.replace(
        "<!-- PENDULO_POWER_FINANCE_EVIDENCE_VERSION:146 -->",
        "<!-- PENDULO_POWER_HORIZONTAL_CONTROLS_VERSION:147 -->",
        1,
    )
    text = re.sub(r"^[ \t]+$", "", text, flags=re.MULTILINE)

    html_ids = re.findall(r'\bid="([^"]+)"', text)
    production_start = text.index('data-pend-layer-panel="production"')
    hero_start = text.index('<section class="pend-card pend-hero">', production_start)
    hero_end = text.index('</section>', hero_start)
    graph_heading_index = text.index("El péndulo distributivo argentino", hero_end)
    controls_index = text.index('class="pend-controls pend-controls-near-chart"', graph_heading_index)
    chart_index = text.index('id="pendMainChart"', controls_index)
    stickers_index = text.index('class="pend-chart-stickers"', graph_heading_index)

    tests = {
        "controls_removed_from_hero": "pend-controls" not in text[hero_start:hero_end],
        "controls_live_inside_main_chart_card": graph_heading_index < stickers_index < controls_index < chart_index,
        "controls_exist_once": text.count('id="pendPerspectiveButtons"') == 1 and text.count('id="pendUniverseButtons"') == 1,
        "average_toggle_joined_to_toolbar": text.count('id="pendAverageToggle"') == 1 and controls_index < text.index('id="pendAverageToggle"') < chart_index,
        "controls_link_to_chart": 'data-controls-for="pendMainChart"' in text,
        "horizontal_nowrap_enabled": ".pend-controls-near-chart .pend-buttons{display:flex;flex-wrap:nowrap" in text,
        "horizontal_scroll_enabled": "scroll-snap-type:x proximity" in HORIZONTAL_CSS,
        "mobile_groups_get_own_rows": "display:grid;grid-template-columns:minmax(0,1fr)" in HORIZONTAL_CSS,
        "layer_nav_stays_horizontal": ".pend-layer-nav{display:flex;flex-wrap:nowrap" in text,
        "cft_preserved": "CFT: la comparación banco–PNFC que sí existe" in text,
        "roa_preserved": "¿La brecha de tasas se volvió ganancia bancaria?" in text,
        "six_layers_preserved": text.count('class="pend-layer-btn') == 6,
        "tab_count_preserved": text.count('class="tab-btn') == source.count('class="tab-btn'),
        "html_ids_unique": len(html_ids) == len(set(html_ids)),
    }
    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise RuntimeError(f"Fallaron tests v147: {failed}")

    OUTPUT_HTML.write_text(text, encoding="utf-8")
    INDEX_HTML.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest()

    audit = f"""# Auditoría · Botoneras horizontales del Péndulo v147

Fecha editorial: 2026-08-21  
Archivo: `data/dashboard_kawaii_147_pendulo_botoneras_horizontales.html`  
SHA-256: `{digest}`

## Cambio de jerarquía visual

- Se retiraron los controles `Ver como` y `Serie` de la tarjeta introductoria.
- Ambos grupos se trasladaron a la tarjeta del gráfico `El péndulo distributivo argentino`.
- El checkbox de promedio por gobierno se convirtió en un tercer grupo de la misma botonera.
- Los stickers quedan como guía previa y el dock completo aparece inmediatamente antes del gráfico.
- En escritorio funciona como una barra horizontal compacta.
- En móvil cada grupo ocupa su propia fila horizontal: `Ver como` y `Serie` permanecen descubiertos, y los botones de cada fila pueden desplazarse lateralmente sin envolver texto.
- La nota secundaria de `Guías` se oculta sólo en móvil para que el checkbox no genere un scrollbar innecesario.
- La navegación de capas A–F conserva el mismo patrón horizontal y pasa a ser sticky dentro del tab.
- No se duplicaron controles ni se modificó su lógica, datos o semántica.

## Controles automáticos

""" + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in tests.items()) + "\n"
    AUDIT_MD.write_text(audit, encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"output": str(OUTPUT_HTML), "sha256": digest, "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
